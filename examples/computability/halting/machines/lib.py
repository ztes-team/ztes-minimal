# Helper functions shared by the specifications of the machines system.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# A Turing machine with two symbols is written in the notation of bbchallenge: one group of six
# characters per state, A, B, C, …, giving for symbol 0 and for symbol 1 what to write, where to move
# (L or R) and the next state; Z is the halting state, "---" an undefined transition. A configuration
# is {"m", "k", "state", "head", "lo", "tape"}: machine m after k steps, the tape holding the cells
# lo … lo + len(tape) − 1, every other cell blank (0).


def table(MACHINE):
    """The transitions of a machine as {"A0": [write, move, next], …}; move is +1 (R) or −1 (L)."""
    out = {}
    parts = MACHINE.split("_")
    for i in range(len(parts)):
        for s in range(2):
            t = parts[i][3 * s: 3 * s + 3]
            key = "ABCDEF"[i] + ("1" if s == 1 else "0")
            out[key] = None if t == "---" else [1 if t[0] == "1" else 0, 1 if t[1] == "R" else -1, t[2]]
    return out


def initial(M):
    """Configuration 0 of machine M: state A, head at cell 0, a blank tape."""
    return {"m": M, "k": 0, "state": "A", "head": 0, "lo": 0, "tape": [0]}


def step(TRANS, c):
    """The configuration after one transition from c (c is not halting)."""
    pos = c["head"] - c["lo"]
    t = TRANS[c["state"] + ("1" if c["tape"][pos] == 1 else "0")]
    tape = [x for x in c["tape"]]
    tape[pos] = t[0]
    head = c["head"] + t[1]
    lo = c["lo"]
    if head < lo:
        tape = [0] + tape
        lo = head
    if head >= lo + len(tape):
        tape = tape + [0]
    return {"m": c["m"], "k": c["k"] + 1, "state": t[2], "head": head, "lo": lo, "tape": tape}


def history(M, K, configs):
    """The recorded configurations of machine M, in order of k."""
    out = []
    for k in range(K + 1):
        if (M, k) not in configs:
            break
        out.append(configs[(M, k)])
    return out


def ones(c):
    """The cells of c that hold a 1, as a list of positions."""
    return [c["lo"] + q for q in range(len(c["tape"])) if c["tape"][q] == 1]


def blank_from(c, x):
    """Is every cell at position x or to its right blank in configuration c?"""
    return all(c["tape"][q] == 0 for q in range(len(c["tape"])) if c["lo"] + q >= x)


def cycle(cs, i, j):
    """Certificate 'cycle': configuration j equals configuration i (state, head and tape), so the
    computation from j repeats that from i forever."""
    return i < j and cs[i]["state"] == cs[j]["state"] and cs[i]["head"] == cs[j]["head"] and ones(cs[i]) == ones(cs[j])


def translated(cs, i, j):
    """Certificate 'translated': at step i every cell from the head to the right is blank; between i
    and j the head never moves left of its position at i; at j the state is the same, the head is
    further right and every cell from it to the right is blank. The computation from j then repeats
    that from i shifted by head_j − head_i, forever."""
    if not (i < j and cs[i]["state"] == cs[j]["state"] and cs[j]["head"] > cs[i]["head"]):
        return False
    if not (blank_from(cs[i], cs[i]["head"]) and blank_from(cs[j], cs[j]["head"])):
        return False
    return all(cs[k]["head"] >= cs[i]["head"] for k in range(i, j + 1))


def certificate(cs, j):
    """A search: the smallest i for which (i, j) is a certificate, as [kind, i]; None if there is none."""
    for i in range(j):
        if cycle(cs, i, j):
            return ["cycle", i]
        if translated(cs, i, j):
            return ["translated", i]
    return None


def checked(cs, w):
    """A check of a given verdict, without search: the halting configuration, or the certificate (i, j)."""
    i = w["i"]
    j = w["j"]
    if not (0 <= i <= j < len(cs)) or w["steps"] != j or w["ones"] != sum(cs[j]["tape"]):
        return False
    if w["kind"] == "halt":
        return w["halts"] and i == j and cs[j]["state"] == "Z"
    if w["halts"] or any(cs[k]["state"] == "Z" for k in range(i, j + 1)):
        return False
    if w["kind"] == "cycle":
        return cycle(cs, i, j)
    if w["kind"] == "translated":
        return translated(cs, i, j)
    return False


def measure(verdicts, configs, profile, profiles):
    """The indicators of the machines execution (KPI abstraction)."""
    rows = {r["abstraction"]: r for r in profile}
    vs = [verdicts[m] for m in sorted(verdicts)]
    return {"profile": profiles, "machines": len(vs), "halting": len([v for v in vs if v["halts"]]),
            "certified": len([v for v in vs if not v["halts"]]), "configurations": len(configs),
            "steps": [v["steps"] for v in vs], "ones": [v["ones"] for v in vs],
            "verdict_invocations": rows["verdict"]["I"], "verdict_not_yet": rows["verdict"]["U"]}
