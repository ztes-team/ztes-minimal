"""Tests of the halting examples (examples/computability/halting): the modalities of Theorem 4.

The record shows each verdict and its evidence. The tests check what it cannot show by itself:
* the champions halt where an independent simulator says;
* the two certified machines indeed do not halt for a long time, and a wrong certificate is refused;
* every Collatz number of the window reaches 1, and the rules of Antihydra are those of bbchallenge;
* finish-unfair and finish-unreachable carry the same payloads, while finish is reachable at every
  prefix of the first and at none of the second.
"""
import json
import shutil

import pytest

from conftest import ROOT, quiet
from ztes import model as evaluation
from ztes.substrate import lookups
from ztes.substrate.replay import verify
from ztes.substrate.store import DiskStore, MemoryStore, read
from ztes.system.report import check_expect
from ztes.system.system import System

HALTING = ROOT / "examples" / "computability" / "halting"
NAMES = ["machines", "collatz", "antihydra", "finish-fair", "finish-unfair", "finish-unreachable"]
EVENTS = {"machines": 183, "collatz": 1009, "antihydra": 1012, "finish-fair": 26, "finish-unfair": 50,
          "finish-unreachable": 50}

_RUNS = {}


def run(name):
    """The record of one system under the agenda (computed once per test session)."""
    if name not in _RUNS:
        system, store = System(HALTING / name), MemoryStore()
        system.run(store, log=quiet)
        _RUNS[name] = (system, list(read(store)))
    return _RUNS[name]


def execs(C, a):
    return [(n, e) for n, e in enumerate(C) if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == a]


def values(C, a):
    return [e["payload"] for _, e in execs(C, a)]


# ---- an independent simulator ----------------------------------------------------------------------

def simulate(machine, limit, keep=True):
    """Run a machine in bbchallenge notation from a blank tape: (halted, steps, ones, history), where
    history[k] = (state, head, sorted cells holding 1) before step k + 1 (kept only if keep)."""
    table = {}
    for i, part in enumerate(machine.split("_")):
        for s in (0, 1):
            t = part[3 * s: 3 * s + 3]
            table["ABCDEF"[i], s] = None if t == "---" else (int(t[0]), 1 if t[1] == "R" else -1, t[2])
    tape, head, state, history = {}, 0, "A", []
    for k in range(limit + 1):
        if keep:
            history.append((state, head, sorted(p for p, v in tape.items() if v)))
        if state == "Z":
            return True, k, sum(tape.values()), history
        write, move, state = table[state, tape.get(head, 0)]
        tape[head] = write
        head += move
    return False, limit, sum(tape.values()), history


# ---- every system --------------------------------------------------------------------------------

@pytest.mark.parametrize("name", NAMES)
def test_halting_example_is_well_formed_and_meets_its_expected_end(name):
    system, C = run(name)
    assert system.check(log=quiet) == []
    assert system.expect and check_expect(system, C, log=quiet) == []
    assert len(C) == EVENTS[name]


@pytest.mark.parametrize("name", NAMES)
def test_halting_example_replays_in_process_and_over_http(name, tmp_path):
    from fastapi.testclient import TestClient
    from ztes.service import HttpService, make_app
    system, C = run(name)
    assert verify(C) == []
    store = DiskStore(tmp_path)
    system = System(HALTING / name)
    system.run(store, {a: HttpService(client=TestClient(make_app(store, a))) for a in system.abstractions}, log=quiet)
    assert [e["payload"] for e in read(store)] == [e["payload"] for e in C]


# ---- machines --------------------------------------------------------------------------------------

def test_the_champions_halt_where_an_independent_simulator_says():
    system, C = run("machines")
    machines = {v: s for v, s in ((m, system.specs[f"run/ontology.v{m}"]["constants"]["MACHINE"]) for m in range(1, 6))}
    configs = values(C, "run")
    for m, (steps, ones) in {1: (6, 4), 2: (21, 5), 3: (107, 13)}.items():
        halted, k, n, history = simulate(machines[m], 1000)
        assert (halted, k, n) == (True, steps, ones)
        recorded = [c for c in configs if c["m"] == m]
        assert [(c["state"], c["head"], [c["lo"] + q for q, x in enumerate(c["tape"]) if x]) for c in recorded] == \
            [(s, h, list(o)) for s, h, o in history]
    assert [v["halts"] for v in values(C, "verdict")] == [True, True, True, False, False]


def test_the_certified_machines_do_not_halt_and_a_wrong_certificate_is_refused():
    """The cycler and the translated cycler run 10⁵ steps without halting. D2: the criterion checks a
    given certificate; one with another pair, or a claim that the machine halts, is refused."""
    system, C = run("machines")
    for m in (4, 5):
        machine = system.specs[f"run/ontology.v{m}"]["constants"]["MACHINE"]
        assert simulate(machine, 100000, keep=False)[0] is False
    for m, kind in ((4, "cycle"), (5, "translated")):
        n, e = next((n, e) for n, e in execs(C, "verdict") if e["payload"]["m"] == m)
        P, good = C[:n], e["payload"]
        assert (good["kind"], good["i"], good["j"]) == (kind, 0, 6)
        tau = lookups.load(P, e["coord"]["criterion"])
        assert evaluation.judge(P, tau, good)
        assert not evaluation.judge(P, tau, dict(good, i=1))
        assert not evaluation.judge(P, tau, dict(good, j=5, steps=5))
        assert not evaluation.judge(P, tau, dict(good, halts=True))


# ---- collatz ---------------------------------------------------------------------------------------

def test_collatz_every_number_of_the_window_reaches_1_and_none_is_checked_twice():
    _, C = run("collatz")
    pieces = values(C, "segment")
    assert [p["n"] for p in pieces] == list(range(1, 1001)) and all(p["below"] for p in pieces)
    for n in range(1, 1001):
        m, k = n, 0
        while m != 1 and k < 10000:
            m, k = (m // 2 if m % 2 == 0 else 3 * m + 1), k + 1
        assert m == 1
    assert sum(len(p["path"]) - 1 for p in pieces) == 5379
    assert values(C, "kpi")[-1]["steps_to_1"] == 59542


def test_collatz_a_piece_must_stop_at_the_first_value_below_its_number():
    _, C = run("collatz")
    n, e = next((n, e) for n, e in execs(C, "segment") if e["payload"]["n"] == 27)
    P, good = C[:n], e["payload"]
    tau = lookups.load(P, e["coord"]["criterion"])
    assert evaluation.judge(P, tau, good) and len(good["path"]) == 97      # 27 falls below itself after 96 steps
    longer = good["path"] + [good["path"][-1] * 3 + 1 if good["path"][-1] % 2 else good["path"][-1] // 2]
    assert not evaluation.judge(P, tau, dict(good, path=longer))
    assert not evaluation.judge(P, tau, dict(good, path=good["path"][:-1]))


def test_collatz_short_pieces_add_up_and_a_piece_has_at_most_L_steps(tmp_path):
    """With L = 2 a number may need several pieces. The indicator adds all of them: for 1, 2 and 3,
    0 + 1 + 7 = 8 steps to 1. A piece that falls below its number in six steps is refused under
    L = 2. (R2 replays the judgments a specification made; it does not show that the specification
    is right. Before this test the indicator counted only the last piece of a number.)"""
    short = tmp_path / "collatz"
    shutil.copytree(HALTING / "collatz", short)
    m = json.loads((short / "system.json").read_text())
    m["constants"]["L"] = 2
    m["plan"][2]["max_admissions"] = 5
    m.pop("expect")
    (short / "system.json").write_text(json.dumps(m))
    system, store = System(short), MemoryStore()
    system.run(store, log=quiet)
    C = list(read(store))
    pieces = values(C, "segment")
    assert [p["path"] for p in pieces] == [[1], [2, 1], [3, 10, 5], [5, 16, 8], [8, 4, 2]]
    assert values(C, "kpi")[-1]["steps_to_1"] == 8 and verify(C) == []
    n, e = execs(C, "segment")[2]
    P = C[:n]
    tau = lookups.load(P, e["coord"]["criterion"])
    assert not evaluation.judge(P, tau, {"n": 3, "path": [3, 10, 5, 16, 8, 4, 2], "below": True})


# ---- antihydra -------------------------------------------------------------------------------------

def test_antihydra_follows_the_rules_and_records_no_verdict():
    _, C = run("antihydra")
    steps = values(C, "rule")
    a, b = 8, 0
    for k, s in enumerate(steps):
        assert (s["k"], s["a"], s["b"]) == (k, a, b)
        b = b + 2 if a % 2 == 0 else b - 1
        a = a + a // 2
    assert len(steps) == 1001 and values(C, "halt") == [] and min(s["b"] for s in steps) == 0


# ---- tick / finish ---------------------------------------------------------------------------------

def test_the_fair_scheduler_finishes_after_an_even_number_of_ticks():
    _, C = run("finish-fair")
    assert [d[0] for d in values(C, "policy")] == [0, 1, 0, 0, 1, 0, 0, 0, 1]
    assert values(C, "tick") == [{"k": k} for k in range(1, 7)] and values(C, "finish") == [{"ticks": 6}]


def test_the_fair_scheduler_is_the_seeded_source_one_decision_at_a_time():
    """draw(SEED, k) equals the k-th occurrence of the source of sources.py, computed from k alone;
    policy proposes a decision only after every recorded decision has been acted on, so at most one
    decision waits at any prefix, and the record is the same under every schedule."""
    from ztes.model.language import SAFE, library
    from ztes.system.sources import RandomSource
    _, C = run("finish-fair")
    n, e = execs(C, "policy")[0]
    draw = library(lookups.load(C[:n], e["coord"]["ontology"])["library"], SAFE)["draw"]
    source = RandomSource(6, 1, 2)
    assert [draw(6, k) for k in range(200)] == [source.next()[0] for _ in range(200)]
    tick = lookups.load(C, lookups.active(C, "tick", "ontology"))
    helpers = library(tick["library"], SAFE)
    for n, e in execs(C, "policy"):
        P = C[:n]
        decisions, ticks = values(P, "policy"), len(values(P, "tick"))
        assert helpers["next_tick"](decisions, ticks) is None                     # nothing waits for a tick
    assert len(C) == 26 and values(C, "finish") == [{"ticks": 6}]


def test_unfair_and_unreachable_have_the_same_payloads_and_different_classes():
    """The same record, two regimes. In finish-unfair the decision is a boundary occurrence: at every
    prefix a decision for finish is admissible, and after an even number of recorded ticks finish
    follows it, so the goal is reachable (Not Yet) at every prefix: an unbounded run of this kind is in
    𝔚. In finish-unreachable the decision is computed and is always tick: no prefix has a realization
    for finish, so the goal is unreachable (False) at every prefix: class 𝔓."""
    _, U = run("finish-unfair")
    _, D = run("finish-unreachable")
    payloads = lambda C: [(e["coord"].get("abstraction"), e["payload"]) for e in C if e["coord"]["kind"] == "exec"]
    assert payloads(U) == payloads(D)
    from ztes.model.language import SAFE, library
    for n, e in execs(U, "policy"):
        P = U[:n]
        omega = lookups.load(P, e["coord"]["ontology"])
        tau = lookups.load(P, e["coord"]["criterion"])
        assert omega.get("boundary") and evaluation.realize(P, omega, [1]) == [1] and evaluation.judge(P, tau, [1])
        finish = lookups.load(P, lookups.active(P, "finish", "ontology"))
        next_finish = library(finish["library"], SAFE)["next_finish"]
        decisions = values(P, "policy")
        ticks = len(values(P, "tick"))
        if ticks == len(decisions) and ticks % 2 == 0:              # every decision acted on, an even count
            assert next_finish(decisions + [[1]], ticks, 0) == {"ticks": ticks}
    for n, e in execs(D, "policy"):
        P = D[:n]
        omega = lookups.load(P, e["coord"]["ontology"])
        assert not omega.get("boundary") and evaluation.realize(P, omega) == [0]
