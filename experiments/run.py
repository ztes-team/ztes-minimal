"""Run one experiment of experiments/README.md and print its answer.

    python experiments/run.py e1            # or e2 … e7; --seeds N for the runs by workers (default 5)

Every experiment follows the same protocol for each of its systems:

    1. phase 3 under one agenda, on a record kept in memory;
    2. R2: the record is replayed from the empty prefix (substrate/replay.py);
    3. phase 3 by workers, one per abstraction, each pausing at random before every invocation, so that
       the race is decided differently in every run; the history of every lineage is compared with
       the run under the agenda;
    4. what the experiment asks, measured on the records, in one table.

Nothing here adds to the model or to Z₀: the systems are specifications, and this script only runs
them and reads their records.
"""
import argparse
import json
import math
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from ztes.substrate.replay import verify          # noqa: E402
from ztes.substrate.store import MemoryStore, read  # noqa: E402
from ztes.system import workers                    # noqa: E402
from ztes.system.system import System              # noqa: E402

quiet = lambda *_: None


# ---- the protocol ----

def histories(C):
    """The history of every lineage: the payloads of its execution events, in order."""
    out = {}
    for e in C:
        if e["coord"]["kind"] == "exec":
            out.setdefault(e["coord"]["abstraction"], []).append(e["payload"])
    return out


def by_agenda(path):
    system, store = System(path), MemoryStore()
    system.run(store, log=quiet)
    return system, read(store)


def by_workers(path, seed):
    rnd = random.Random(seed)
    system, store = System(path), MemoryStore()
    workers.run(system, store, log=quiet, hesitate=lambda: time.sleep(rnd.random() * 0.003), timeout=600.0)
    return system, read(store)


def protocol(path, seeds):
    """Runs 1–3 of the protocol; returns the record under the agenda, the records by workers, and a summary."""
    system, C = by_agenda(path)
    problems = verify(C)
    central = histories(C)
    runs = [by_workers(path, s)[1] for s in range(seeds)]
    same = sum(1 for R in runs if histories(R) == central)
    replay = all(verify(R) == [] for R in runs)
    return system, C, runs, {"events": len(C), "R2": "OK" if not problems else problems[0],
                             "workers": f"{same}/{seeds} identical", "R2 by workers": "OK" if replay else "FAILED"}


def table(rows, head):
    widths = [max(len(str(r[i])) for r in rows + [head]) for i in range(len(head))]
    line = lambda r: "  " + "  ".join(str(x).ljust(w) for x, w in zip(r, widths))
    print(line(head))
    print("  " + "  ".join("-" * w for w in widths))
    for r in rows:
        print(line(r))


def title(text):
    print("\n" + text)


# ---- Ackermann: the justification of a value, read from the record ----

def ackermann_values(C):
    """(m, n) → (position, value), from the lineage `value`."""
    return {(e["payload"]["m"], e["payload"]["n"]): (p, e["payload"]["v"]) for p, e in enumerate(C)
            if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == "value"}


def ackermann_premises(key, vals):
    """The recorded values on which the criterion of `value` admitted A(m, n): its positive atoms."""
    m, n = key
    if m == 0:
        return []
    if n == 0:
        return [(m - 1, 1)]
    return [(m, n - 1), (m - 1, vals[(m, n - 1)][1])]


def ackermann_measures(vals, root):
    """Depth of the justification of root (longest chain of premises) and the size of its unfolding (the calls of naive recursion)."""
    depth, size = {}, {}
    for key in sorted(vals, key=lambda k: vals[k][0]):         # premises are recorded before their conclusions
        ps = ackermann_premises(key, vals)
        depth[key] = 1 + max((depth[p] for p in ps), default=0)
        size[key] = 1 + sum(size[p] for p in ps)
    return depth[root], size[root]


def naive_ackermann(m, n):
    if m == 0:
        return n + 1
    if n == 0:
        return naive_ackermann(m - 1, 1)
    return naive_ackermann(m - 1, naive_ackermann(m, n - 1))


# ---- the experiments ----

def e1(seeds):
    title("E1. A loop without a loop: while x ≠ 1 do x := collatz(x), from 27")
    system, C, runs, s = protocol(HERE / "e1-loop" / "while-do", seeds)
    h = histories(C)
    exit_at = h["exit"][0]["k"]
    print(f"  the body has no while; the loop is the record of three relations")
    table([[exit_at, max(x["x"] for x in h["state"]), sum(1 for v in h["guard"] if v["v"]),
            sum(1 for v in h["guard"] if not v["v"]), s["events"], s["R2"], s["workers"]]],
          ["steps", "max x", "guard true", "guard false", "events", "R2", "by workers"])
    print("  the exit reads one recorded fact, guard(111) = false: a recorded no, not a missing yes")


def e2(seeds):
    title("E2. The end is recorded: a stream of 8 items, summed")
    rows = []
    for name, how in [("iteration", "the end is a fact: more(8) = false"),
                      ("iteration-absence", "the end is read from an absence (control)")]:
        system, C, runs, s = protocol(HERE / "e2-end" / name, seeds)
        agenda = histories(C)["result"][0]
        seen = sorted({json.dumps(histories(R)["result"][0], sort_keys=True) for R in runs})
        rows.append([name, how, f"{agenda['s']} (n = {agenda['n']})",
                     ", ".join(f"{json.loads(x)['s']} (n = {json.loads(x)['n']})" for x in seen), s["R2"], s["workers"]])
    table(rows, ["system", "end", "sum by agenda", "sums by workers", "R2", "by workers"])
    print("  the control passes R2 in every run: each judgment was true on its prefix; replay cannot see an")
    print("  end read from silence, only Principle R excludes it")


def e3(seeds):
    title("E3. Recursion: the record is both the memo and the stack")
    system, C, runs, s = protocol(HERE / "e3-recursion" / "ackermann", seeds)
    vals = ackermann_values(C)
    start = next(p for p, e in enumerate(C) if e["coord"]["kind"] == "exec")
    govern = next(p for p, e in enumerate(C) if p > start and e["coord"]["kind"] != "exec")   # the governed change
    first = {k for k, (p, v) in vals.items() if p < govern}
    rows = []
    for root, new, held in [((3, 4), len(first), len(first)), ((3, 5), len(vals) - len(first), len(vals))]:
        depth, unfolded = ackermann_measures(vals, root)
        rows.append([f"A{root} = {vals[root][1]}", new, held, unfolded, depth])
    table(rows, ["root", "new values", "values in the record", "calls of naive recursion", "depth of justification"])
    print(f"  one record: {s['events']} events, R2 {s['R2']}, by workers {s['workers']}")
    print(f"  A(3, 5) after A(3, 4) adds {rows[1][1]} values; alone it needs {len(vals)}, since A(3, 4) is part of it")
    title("   without a stack: A(3, 7)")
    system, C = by_agenda(HERE / "e3-recursion" / "ackermann-deep")
    vals = ackermann_values(C)
    depth, unfolded = ackermann_measures(vals, (3, 7))
    try:
        naive = naive_ackermann(3, 7)
        python = f"{naive}"
    except RecursionError:
        python = f"RecursionError (limit {sys.getrecursionlimit()})"
    table([[f"A(3, 7) = {vals[(3, 7)][1]}", len(vals), depth, len(C), "OK" if verify(C) == [] else "FAILED", python]],
          ["ZTES", "values", "depth", "events", "R2", "naive recursion in Python"])


def e4(seeds):
    title("E4. Only what is demanded is computed; a cycle ends in a quiescent record")
    system, C, runs, s = protocol(HERE / "e4-demand" / "sparse", seeds)
    h = histories(C)
    root = h["call"][0]["n"]
    count = {}
    for n in sorted({c["n"] for c in h["call"]}):                    # calls of naive recursion, by the same recurrence
        count[n] = 1 if n == 0 else 1 + count[n // 2] + count[n // 3]
    table([[f"f({root:,}) = {h['result'][0]['v']:,}", len(h["value"]), f"{root + 1:,}", f"{count[root]:,}",
            s["events"], s["R2"], s["workers"]]],
          ["result", "values", "table bottom-up", "calls of naive recursion", "events", "R2", "by workers"])
    system, C, runs, s = protocol(HERE / "e4-demand" / "cycle", seeds)
    h = histories(C)
    states = system.states(C)
    table([[len(h.get("call", [])), len(h.get("value", [])), len(h.get("result", [])), s["events"],
            ", ".join(f"{a}: {st}" for a, st in states.items()), s["R2"], s["workers"]]],
          ["calls", "values", "results", "events", "end", "R2", "by workers"])
    print("  no call is made twice, so the cycle leaves a finite record in which nothing can be admitted:")
    print("  a terminal record in which the goal is not established, status False (class 𝔓 of Theorem 4)")


def instance(m, n, where):
    """The system of ackermann-deep with the root (m, n), written to a temporary directory."""
    path = Path(where) / f"ackermann-{m}-{n}"
    shutil.copytree(HERE / "e3-recursion" / "ackermann-deep", path)
    spec = json.loads((path / "system.json").read_text(encoding="utf8"))
    spec.update(system=path.name, expect={})
    spec["constants"].update(M0=m, N0=n)
    (path / "system.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf8")
    return by_agenda(path)[1]


def e5(seeds):
    title("E5. Self-similarity of the record of a recursion")
    roots = [(1, 5), (2, 5), (2, 13), (2, 29), (3, 2), (3, 3), (3, 4), (3, 5)]
    with tempfile.TemporaryDirectory() as tmp:
        vals = {r: ackermann_values(instance(*r, tmp)) for r in roots}
    print("  (a) the structure below value(m, n) in a larger record is the whole record of A(m, n) run alone")

    def below(key, v):
        seen, stack, edges = set(), [key], set()
        while stack:
            k = stack.pop()
            if k not in seen:
                seen.add(k)
                for p in ackermann_premises(k, v):
                    edges.add((k, p))
                    stack.append(p)
        return seen, edges
    rows = []
    for big, small in [((3, 5), (3, 4)), ((3, 4), (3, 3)), ((3, 4), (3, 2)), ((3, 4), (2, 29)), ((3, 3), (2, 29)),
                       ((3, 3), (2, 13)), ((3, 2), (2, 13)), ((2, 13), (2, 5)), ((2, 5), (1, 5))]:
        inside, alone = below(small, vals[big]), below(small, vals[small])
        same = inside == alone and set(vals[small]) == alone[0] and all(vals[big][k][1] == vals[small][k][1] for k in alone[0])
        rows.append([f"A{small}", f"A{big}", len(alone[0]), "equal" if same else "DIFFERENT"])
    table(rows, ["structure of", "inside the record of", "values", "compared with its own record"])
    print("\n  (b) each record is the beginning of the next one, and twice as long")
    rows = []
    series = [(3, 2), (3, 3), (3, 4), (3, 5)]
    for i, r in enumerate(series):
        order = [k for k in sorted(vals[r], key=lambda k: vals[r][k][0])]
        prefix = "-" if i == 0 else ("yes" if order[:len(vals[series[i - 1]])] == sorted(vals[series[i - 1]], key=lambda k: vals[series[i - 1]][k][0]) else "NO")
        reach = []
        for k, (p, v) in vals[r].items():
            reach += [p - vals[r][q][0] for q in ackermann_premises(k, vals[r])]
        octaves = [sum(1 for d in reach if 2 ** o <= d < 2 ** (o + 1)) for o in range(11)]
        rows.append([f"A{r}", len(vals[r]), prefix, " ".join(f"{c:3}" for c in octaves)])
    table(rows, ["record of", "values", "begins with the one above", "how far back a judgment reads: 2⁰ 2¹ … 2¹⁰"])
    print("\n  (c) growth with the depth of justification: the record and its unfolding")
    rows = []
    for a, b in zip(series, series[1:]):
        (da, ua), (db, ub) = ackermann_measures(vals[a], a), ackermann_measures(vals[b], b)
        rows.append([f"A{a} → A{b}", f"{math.log(len(vals[b]) / len(vals[a])) / math.log(db / da):.2f}",
                     f"{math.log(ub / ua) / math.log(db / da):.2f}"])
    table(rows, ["step", "exponent of the record", "exponent of the unfolded justification"])
    print("  the record is a one-dimensional image of a self-similar justification of dimension two")


def levels(C):
    """Per depth of the tree, the number of nodes that split."""
    out = {}
    for e in C:
        if e["coord"]["kind"] == "exec" and e["payload"].get("kind") == "split":
            d = len(e["payload"]["path"]) - 1
            out[d] = out.get(d, 0) + 1
    return [out.get(d, 0) for d in range(max(out) + 1)]


def exponent(counts):
    """Least-squares slope of log₂(splits) per level, over the levels from the first third to the last two:
    past the coarse start, before the cut-off where the margin of p dominates."""
    xs = list(range(len(counts) // 3, len(counts) - 2))
    ys = [math.log2(counts[x]) for x in xs]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def nodes(C):
    return {e["payload"]["path"] for e in C if e["coord"]["kind"] == "exec" and "path" in e["payload"]}


def root_verdict(C):
    r = [e["payload"] for e in C if e["coord"]["kind"] == "exec" and e["payload"].get("path") == "n"
         and e["payload"]["kind"] != "split"]
    return f"{r[0]['v']}" + ("" if r[0]["v"] else f", witness x = {r[0]['x']}") if r else "Not Yet"


def e6(seeds):
    title("E6. Decomposition: each subproblem a new abstraction with the specialized criterion")
    rows = []
    for name, k in [("split", 2), ("split-quartic", 4)]:
        if name == "split":                                      # by workers: one per node, about 15 s a run
            system, C, runs, s = protocol(HERE / "e6-decomposition" / name, min(seeds, 2))
            by = s["workers"]
        else:                                                    # 1381 nodes: under the agenda only, about a minute
            system, C = by_agenda(HERE / "e6-decomposition" / name)
            by = "not run"
        counts = levels(C)
        rows.append([name, k, root_verdict(C), len(nodes(C)), len(C), " ".join(map(str, counts)),
                     f"{exponent(counts):.2f}", f"{1 - 1 / k:.2f}", "OK" if verify(C) == [] else "FAILED", by])
    table(rows, ["system", "contact k", "p > 0", "new abstractions", "events", "splits per level", "exponent",
                 "predicted 1 − 1/k", "R2", "by workers"])
    print("  the tree refines where the criterion cannot yet certify, by a law fixed in advance by k")
    title("   a root of p: return at once and abandon the rest (variant 3), or wait for both children (variant 1)")
    rows = []
    for name, how in [("split-witness", "3: short-circuit, abandon"), ("split-witness-full", "1: wait for both (control)")]:
        system, C, runs, s = protocol(HERE / "e6-decomposition" / name, seeds)
        verdicts = sorted({root_verdict(R) for R in runs})
        rows.append([name, how, root_verdict(C), "; ".join(verdicts), s["events"],
                     ", ".join(str(len(R)) for R in runs), s["R2"], s["workers"]])
    table(rows, ["system", "variant", "agenda", "by workers", "events (agenda)", "events (workers)", "R2", "by workers"])
    print("  variant 3: the verdict is fixed, the abandoned work depends on the schedule (Corollary 7);")
    print("  variant 1: every node reads a complete horizon, so every lineage has the same history (Theorem K)")


def e7(seeds):
    title("E7. Four fates of an execution (Theorem 4), each read from its record")
    rows = []
    for path, goal, what in [("e1-loop/while-do", "exit", "the loop has ended"),
                             ("e7-fates/sqrt2-digits", "goal", "the first 10 digits of √2 are recorded"),
                             ("e4-demand/cycle", "result", "f(0) has a value"),
                             ("e7-fates/goldbach", "goal", "a counterexample to Goldbach is recorded")]:
        system, C = by_agenda(HERE / path)
        window = next((s["max_admissions"] for s in system.plan if s.get("max_admissions")), system.admission_limit)
        admitted = sum(1 for e in C if e["coord"]["kind"] == "exec")
        terminal = admitted < window                             # the run ended before its window of observation
        at = next((p for p, e in enumerate(C) if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == goal), None)
        status = "True" if at is not None else ("False" if terminal else "Not Yet")
        fate = {("True", True): "𝔗 terminating solution", ("True", False): "𝔒 ontological infinity",
                ("False", True): "𝔓 pathological non-progress", ("Not Yet", False): "𝔚 perpetual Not Yet"}[(status, terminal)]
        rows.append([Path(path).name, what, status + ("" if at is None else f" at C^{at}"),
                     "yes" if terminal else f"no: {window} admissions observed", fate,
                     "OK" if verify(C) == [] else "FAILED"])
    table(rows, ["system", "goal", "status of the goal", "terminal", "class", "R2"])
    print("  True: the goal is a recorded fact; False: the record is terminal and the goal is not in it;")
    print("  Not Yet: neither, and nothing recorded excludes it. Infinity is never admitted, only continued.")


EXPERIMENTS = {"e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "e6": e6, "e7": e7}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("experiment", choices=sorted(EXPERIMENTS) + ["all"])
    parser.add_argument("--seeds", type=int, default=5, help="runs by workers (default 5)")
    args = parser.parse_args()
    for name in (sorted(EXPERIMENTS) if args.experiment == "all" else [args.experiment]):
        EXPERIMENTS[name](args.seeds)
