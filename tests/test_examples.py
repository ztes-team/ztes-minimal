import tempfile
"""Tests of the examples: each run is compared with the "Expected end" section of its DESIGN.md."""
from pathlib import Path

import pytest

from ztes import model as evaluation
from ztes.system.system import System
from ztes.substrate import lookups
from ztes.substrate.store import DiskStore, read
from ztes.substrate.replay import verify

EXAMPLES = Path(__file__).parent.parent / "examples"
NAMES = ["sqrt2", "dedekind-cut", "prime-witnesses", "factorization", "payment", "tsp", "tsp-bnb",
         "aco", "aco-draw"]
quiet = lambda *_: None


def run(name, tmp_path, services=None):
    system = System(EXAMPLES / name)
    store = DiskStore(tmp_path)
    system.run(store, services, log=quiet)
    C = read(store)
    return system, C


def values(C, a):
    return [e["payload"] for e in C if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == a]


@pytest.mark.parametrize("name", NAMES)
def test_example_is_well_formed(name):
    assert System(EXAMPLES / name).check(log=quiet) == []


@pytest.mark.parametrize("name", NAMES)
def test_example_meets_its_expected_end(name, tmp_path):
    """Every example states its expected end in system.json ("expect"); the run must meet it."""
    from ztes.system.report import check_expect
    system, C = run(name, tmp_path)
    assert system.expect, f"{name} has no expect"
    assert check_expect(system, C, log=quiet) == []


@pytest.mark.parametrize("name,events", [("sqrt2", 16), ("dedekind-cut", 26), ("prime-witnesses", 26),
                                         ("factorization", 27), ("payment", 21), ("tsp", 468),
                                         ("tsp-bnb", 71), ("aco", 73), ("aco-draw", 138)])
def test_every_example_replays(name, events, tmp_path):
    """R2 for every example, in-process and over HTTP (the candidate travels as JSON)."""
    from fastapi.testclient import TestClient
    from ztes.service import HttpService, make_app
    _, C = run(name, tmp_path / "local")
    assert verify(C) == [] and len(C) == events
    system = System(EXAMPLES / name)
    store = DiskStore(tmp_path / "http")
    system.run(store, {a: HttpService(client=TestClient(make_app(store, a))) for a in system.abstractions}, log=quiet)
    assert [e["payload"] for e in read(store)] == [e["payload"] for e in C]


def test_dedekind_cut_repair(tmp_path):
    """Before the repair intervals waits on the external lineage; the repair is recorded before the first interval."""
    system = System(EXAMPLES / "dedekind-cut")
    system.plan = system.plan[:3]                      # up to the first termination, before the repair
    store = DiskStore(tmp_path / "before")
    system.run(store, log=quiet)
    C = read(store)
    assert values(C, "intervals") == []
    assert system.states(C) == {"denominators": "closed", "bounds": "wait", "intervals": "wait-external"}

    system, C = run("dedekind-cut", tmp_path / "after")
    repair = [n for n, e in enumerate(C) if e["coord"]["kind"] == "spec" and e["coord"]["version"] == 2]
    first_interval = min(n for n, e in enumerate(C) if e["coord"].get("abstraction") == "intervals"
                         and e["coord"]["kind"] == "exec")
    assert repair and repair[0] < first_interval      # recorded before it takes effect (S1.3, S1.5)


def test_factor_criterion_rejects_a_false_certificate(tmp_path):
    """D2: the criterion checks a certificate without search; wrong ones are refused."""
    _, C = run("factorization", tmp_path)
    i = max(n for n, e in enumerate(C) if e["coord"].get("abstraction") == "factor" and e["coord"]["kind"] == "exec")
    P, good = C[:i], C[i]["payload"]                   # h₄ and the prefix on which it was judged
    tau = lookups.load(P, lookups.active(P, "factor", "criterion"))
    assert good["n"] == 7429 and evaluation.judge(P, tau, good)
    assert not evaluation.judge(P, tau, dict(good, factors=[17, 437]))   # product right, 437 = 19 · 23 uncertified
    assert not evaluation.judge(P, tau, dict(good, reused=30030))         # wrong provenance


def test_payment_grounds_are_in_the_evidence(tmp_path):
    """§1.3: equal payloads, different grounds; without the override the same judgment fails."""
    system, C = run("payment", tmp_path)
    t = [n for n, e in enumerate(C) if e["coord"].get("abstraction") == "transfer" and e["coord"]["kind"] == "exec"]
    assert len(t) == 2 and C[t[0]]["payload"] == C[t[1]]["payload"] == {"from": "a", "to": "b", "amount": 50}
    assert C[t[0]] != C[t[1]]                          # e ≠ e′ although U(e) = U(e′)
    P = C[:t[1]]
    tau = lookups.load(P, C[t[1]]["coord"]["criterion"])
    assert evaluation.judge(P, tau, C[t[1]]["payload"])
    without_override = [e for e in P if e["coord"].get("abstraction") != "override"]
    assert not evaluation.judge(without_override, tau, C[t[1]]["payload"])
    assert system.states(C) == {"requests": "wait", "fraud_check": "wait", "override": "wait", "transfer": "closed"}


def test_tsp_is_optimal_and_reuses_recorded_subproblems(tmp_path):
    """The tours are optimal (independent brute force), and later questions reuse the record."""
    from itertools import permutations
    system, C = run("tsp", tmp_path)
    XY = system.definition["constants"]["XY"]
    d = lambda a, b: abs(XY[a][0] - XY[b][0]) + abs(XY[a][1] - XY[b][1])
    for t in values(C, "tour"):
        rest = [c for c in t["cities"] if c != 0]
        best = min(sum(d(p[i], p[i + 1]) for i in range(len(p) - 1)) for p in ([0, *q, 0] for q in permutations(rest)))
        assert t["length"] == best
    at = [n for n, e in enumerate(C) if e["coord"].get("abstraction") == "tour" and e["coord"]["kind"] == "exec"]
    new = [sum(1 for e in C[a:b] if e["coord"].get("abstraction") == "dp" and e["coord"]["kind"] == "exec")
           for a, b in zip([0] + at, at)]
    assert new == [192, 256, 0]                        # instance 2 reuses 192, instance 3 reuses all 80
    keys = [(e["payload"]["mask"], e["payload"]["j"]) for e in C if e["coord"].get("abstraction") == "dp"
            and e["coord"]["kind"] == "exec"]
    assert len(keys) == len(set(keys)) == 448          # no subproblem is ever computed twice


def test_tsp_bnb_prunes_by_recorded_bounds(tmp_path):
    """Branch and bound: optimal tours, proofs checked against the record, and the seed's effect."""
    from itertools import permutations
    from math import factorial
    from ztes.system.authoring import read_directory
    from ztes.substrate.store import MemoryStore
    system, C = run("tsp-bnb", tmp_path)
    XY = system.definition["constants"]["XY"]
    d = lambda a, b: abs(XY[a][0] - XY[b][0]) + abs(XY[a][1] - XY[b][1])
    proofs = values(C, "proof")
    for p in proofs:
        best = min(sum(d(t[i], t[i + 1]) for i in range(len(t) - 1))
                   for t in ([0, *q, 0] for q in permutations(range(1, p["n"]))))
        assert p["length"] == best
        full_tree = sum(factorial(p["n"] - 1) // factorial(p["n"] - 1 - k) for k in range(p["n"] - 1))
        assert p["expanded"] < full_tree / 30           # 34 of 1,237 and 14 of 8,660
    assert [p["expanded"] for p in proofs] == [34, 14]
    defn = read_directory(EXAMPLES / "tsp-bnb")         # the same plan without the seed
    defn["specifications"]["best/ontology.v2"] = dict(defn["specifications"]["best/ontology.v1"], constants={"N": 8})
    s = System.from_dict(defn)
    st = MemoryStore()
    s.run(st, log=quiet)
    assert [p["expanded"] for p in values(read(st), "proof")] == [34, 16]


def test_tsp_order_extends_when_a_city_is_added():
    """The order in which dp records subproblems for N-1 cities is a prefix of the order for N."""
    from ztes.model.language import library
    from ztes.model.language import SAFE
    lib = library((EXAMPLES / "tsp" / "lib.py").read_text(encoding="utf8"), SAFE)
    for n in range(3, 10):
        small, large = lib["order"](n), lib["order"](n + 1)
        assert large[:len(small)] == small
        pos = {x: i for i, x in enumerate(large)}
        for m, j in large:                                       # every predecessor comes first
            prev = m ^ (1 << j)
            assert all(pos[(prev, i)] < pos[(m, j)] for i in lib["bits"](prev, n + 1)) if prev else True



def test_tsp_kpi_measures_reuse_on_demand():
    """The KPI abstraction of tsp, invoked once at the end, measures the reuse of recorded subproblems."""
    system = System(EXAMPLES / "tsp")
    store = DiskStore(tempfile.mkdtemp())
    system.run(store, log=lambda *_: None)
    from ztes.system.kpi import table
    rows, kpi = table(system, read(store))
    assert (kpi["subproblems"], kpi["needed"], kpi["saved"]) == (448, 720, 272)
    assert (kpi["tour_invocations"], kpi["tour_not_yet"]) == (rows["tour"]["I"], rows["tour"]["U"]) == (230, 227)


def _optimum(D):
    """Held–Karp, written independently of the examples."""
    from itertools import combinations
    n, best = len(D), {}
    for j in range(1, n):
        best[(1 << j, j)] = D[0][j]
    for size in range(2, n):
        for S in combinations(range(1, n), size):
            mask = sum(1 << j for j in S)
            for j in S:
                best[(mask, j)] = min(best[(mask ^ (1 << j), k)] + D[k][j] for k in S if k != j)
    return min(best[((1 << n) - 2, j)] + D[j][0] for j in range(1, n))


@pytest.mark.parametrize("name", ["aco", "aco-draw"])
def test_aco_tours_are_valid_and_measured_against_the_exact_optimum(name, tmp_path):
    system, C = run(name, tmp_path)
    c = system.definition["constants"]
    XY, N = c["XY"], c["N"]
    D = [[abs(XY[a][0] - XY[b][0]) + abs(XY[a][1] - XY[b][1]) for b in range(N)] for a in range(N)]
    assert c["OPT"] == _optimum(D)                           # the constant the KPI compares with
    tours, best, kpi = values(C, "tour"), values(C, "best"), values(C, "kpi")[-1]
    assert len(tours) == c["T"] and [t["k"] for t in tours] == list(range(c["T"]))
    for t in tours:
        assert sorted(t["walk"]) == list(range(N))
        assert t["length"] == sum(D[t["walk"][i - 1]][t["walk"][i]] for i in range(N))
    assert [b["length"] for b in best] == sorted({b["length"] for b in best}, reverse=True)   # only improvements
    assert best[-1]["length"] == min(t["length"] for t in tours) == kpi["best"] >= c["OPT"]
    assert best[-1]["k"] == next(t["k"] for t in tours if t["length"] == kpi["best"])          # the earliest shortest


def test_aco_quota_needs_no_draw_and_is_a_function_of_the_record(tmp_path):
    """The quota colony has no source of chance: two runs give the same record, event for event."""
    _, C1 = run("aco", tmp_path / "a")
    _, C2 = run("aco", tmp_path / "b")
    assert [e["payload"] for e in C1] == [e["payload"] for e in C2]
    assert not System(EXAMPLES / "aco").declared_sources


def test_aco_draws_are_recorded_and_replay_never_asks_the_source(tmp_path):
    """Chance enters as a boundary abstraction: T admitted draws, one per ant; R2 reads them from C."""
    from ztes.system.authoring import read_directory
    from ztes.substrate.store import MemoryStore
    system, C = run("aco-draw", tmp_path)
    c = system.definition["constants"]
    draws = values(C, "draw")
    assert len(draws) == c["T"] and all(len(r) == c["N"] - 1 and all(0 <= v < c["M"] for v in r) for r in draws)
    assert verify(C) == []                                   # no source exists here: the record suffices
    assert system.states(C)["draw"] == "closed"              # the budget closes the lineage (τ false)
    defn = read_directory(EXAMPLES / "aco-draw")             # another seed: other draws, another record
    defn["sources"]["draw"]["random"]["seed"] = 2
    store = MemoryStore()
    System.from_dict(defn).run(store, log=quiet)
    assert values(read(store), "draw") != draws and verify(read(store)) == []


def test_a_source_is_declared_for_a_boundary_abstraction_only():
    from ztes.system.authoring import read_directory
    defn = read_directory(EXAMPLES / "aco-draw")
    defn["sources"] = {"tour": defn["sources"]["draw"], "nobody": {"random": {"seed": 1, "size": 1, "below": 2}}}
    found = "\n".join(System.from_dict(defn).check(log=quiet))
    assert "tour has a source but its ontology is not a boundary ontology" in found
    assert "nobody is not an abstraction of the system" in found
