"""Tests of the experiments (experiments/README.md): each system meets its expected end and replays, the
designs in normal form give the same history of every lineage under random schedules, and each
experiment measures what it claims."""
import random
import sys
import time
from pathlib import Path

import pytest

from conftest import ROOT, quiet
from ztes.substrate.replay import verify
from ztes.substrate.store import MemoryStore, read
from ztes.system import workers
from ztes.system.report import check_expect
from ztes.system.system import System

EXP = ROOT / "experiments"
sys.path.insert(0, str(EXP))
import run as experiments                                    # noqa: E402  the protocol of experiments/run.py

SYSTEMS = ["e1-loop/while-do", "e2-end/iteration", "e2-end/iteration-absence", "e3-recursion/ackermann",
           "e3-recursion/ackermann-deep", "e4-demand/sparse", "e4-demand/cycle"]
NORMAL_FORM = ["e1-loop/while-do", "e2-end/iteration", "e3-recursion/ackermann", "e4-demand/sparse", "e4-demand/cycle"]


def by_agenda(name):
    system, store = System(EXP / name), MemoryStore()
    system.run(store, log=quiet)
    return system, read(store)


def by_workers(name, seed):
    rnd = random.Random(seed)
    system, store = System(EXP / name), MemoryStore()
    workers.run(system, store, log=quiet, hesitate=lambda: time.sleep(rnd.random() * 0.003), timeout=600.0)
    return read(store)


@pytest.mark.parametrize("name", SYSTEMS)
def test_experiment_system_meets_its_expected_end_and_replays(name):
    assert System(EXP / name).check(log=quiet) == []          # before a run brings in abstractions of its own
    system, C = by_agenda(name)
    assert check_expect(system, C, log=quiet) == []
    assert verify(C) == []                                   # R2


@pytest.mark.parametrize("name", NORMAL_FORM)
def test_normal_form_gives_the_same_history_of_every_lineage(name):
    """Theorem K, executed: every criterion reads other lineages through positive atoms only."""
    _, C = by_agenda(name)
    for seed in range(2):
        R = by_workers(name, seed)
        assert verify(R) == []
        assert experiments.histories(R) == experiments.histories(C)


def test_e1_the_loop_ends_on_a_recorded_no():
    _, C = by_agenda("e1-loop/while-do")
    h = experiments.histories(C)
    assert h["exit"] == [{"k": 111}] and h["state"][-1] == {"k": 111, "x": 1}
    assert [v["v"] for v in h["guard"]] == [True] * 111 + [False]


def test_e2_an_end_read_from_an_absence_depends_on_the_schedule_and_replays_anyway():
    """Principle R: the control admits on an absence; R2 cannot see it, the schedule changes it."""
    _, C = by_agenda("e2-end/iteration-absence")
    assert experiments.histories(C)["result"] == [{"n": 1, "s": 5}] and verify(C) == []
    seen = set()
    for seed in range(3):
        R = by_workers("e2-end/iteration-absence", seed)
        assert verify(R) == []
        seen.add(tuple(sorted(experiments.histories(R)["result"][0].items())))
    assert seen != {(("n", 1), ("s", 5))}
    _, N = by_agenda("e2-end/iteration")
    assert experiments.histories(N)["result"] == [{"n": 8, "s": 39}]


def test_e3_values_are_recorded_once_and_a_later_root_continues_the_record():
    _, C = by_agenda("e3-recursion/ackermann")
    vals = experiments.ackermann_values(C)
    start = next(p for p, e in enumerate(C) if e["coord"]["kind"] == "exec")
    govern = next(p for p, e in enumerate(C) if p > start and e["coord"]["kind"] != "exec")
    first = [k for k, (p, v) in vals.items() if p < govern]
    assert len(first) == 315 and len(vals) == 636 and len(vals) - len(first) == 321
    assert experiments.ackermann_measures(vals, (3, 4)) == (127, 10307)
    assert experiments.ackermann_measures(vals, (3, 5)) == (255, 42438)


def test_e3_depth_without_a_stack():
    _, C = by_agenda("e3-recursion/ackermann-deep")
    vals = experiments.ackermann_values(C)
    assert vals[(3, 7)][1] == 1021 and experiments.ackermann_measures(vals, (3, 7))[0] == 1023
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)
    try:
        with pytest.raises(RecursionError):
            experiments.naive_ackermann(3, 7)
    finally:
        sys.setrecursionlimit(limit)


def test_e4_only_demanded_arguments_and_a_quiescent_cycle():
    _, C = by_agenda("e4-demand/sparse")
    h = experiments.histories(C)
    assert len(h["value"]) == 242 and h["result"] == [{"v": 18639940}]
    system, C = by_agenda("e4-demand/cycle")
    h = experiments.histories(C)
    assert len(h["call"]) == 2 and "value" not in h and "result" not in h
    assert set(system.states(C).values()) == {"wait"}


SYSTEMS_E6_E7 = ["e6-decomposition/split", "e6-decomposition/split-witness", "e6-decomposition/split-witness-full",
                 "e7-fates/sqrt2-digits", "e7-fates/goldbach"]


@pytest.mark.parametrize("name", SYSTEMS_E6_E7)
def test_experiment_system_e6_e7_meets_its_expected_end_and_replays(name):
    test_experiment_system_meets_its_expected_end_and_replays(name)


def test_e5_the_record_of_a_recursion_contains_itself():
    with experiments.tempfile.TemporaryDirectory() as tmp:
        vals = {r: experiments.ackermann_values(experiments.instance(*r, tmp)) for r in [(1, 5), (2, 5), (3, 2), (3, 3)]}

    def below(key, v):
        seen, stack = set(), [key]
        while stack:
            k = stack.pop()
            if k not in seen:
                seen.add(k)
                stack += experiments.ackermann_premises(k, v)
        return seen
    for big, small in [((2, 5), (1, 5)), ((3, 3), (3, 2))]:
        assert below(small, vals[big]) == below(small, vals[small]) == set(vals[small])
        assert all(vals[big][k][1] == vals[small][k][1] for k in vals[small])
    order = lambda v: sorted(v, key=lambda k: v[k][0])
    assert order(vals[(3, 3)])[:len(vals[(3, 2)])] == order(vals[(3, 2)])           # a prefix, about twice as long
    assert (len(vals[(3, 2)]), len(vals[(3, 3)])) == (73, 154)


def test_e6_decomposition_returns_upward_and_its_front_has_the_predicted_exponent():
    _, C = by_agenda("e6-decomposition/split")
    assert experiments.root_verdict(C) == "True" and len(experiments.nodes(C)) == 183
    counts = experiments.levels(C)
    assert counts == [1, 2, 3, 4, 6, 9, 12, 16, 20, 18] and abs(experiments.exponent(counts) - 0.5) < 0.02
    R = by_workers("e6-decomposition/split", 0)                     # a worker per node, brought in during the run
    assert experiments.histories(R) == experiments.histories(C) and verify(R) == []


def test_e6_contact_of_order_four_gives_the_exponent_three_quarters():
    _, C = by_agenda("e6-decomposition/split-quartic")
    counts = experiments.levels(C)
    assert counts == [1, 2, 4, 8, 15, 27, 44, 70, 112, 175, 232] and abs(experiments.exponent(counts) - 0.75) < 0.02
    assert experiments.root_verdict(C) == "True" and verify(C) == []


def test_e6_short_circuit_fixes_the_verdict_and_waiting_fixes_every_lineage():
    _, C = by_agenda("e6-decomposition/split-witness")
    assert experiments.root_verdict(C) == "False, witness x = 5/16" and len(C) == 30
    for seed in range(2):
        R = by_workers("e6-decomposition/split-witness", seed)
        assert experiments.root_verdict(R).startswith("False, witness") and verify(R) == []
    _, F = by_agenda("e6-decomposition/split-witness-full")
    assert experiments.root_verdict(F) == "False, witness x = 5/16" and len(F) == 124
    for seed in range(5):                                           # also: no run ends before its new abstractions act
        R = by_workers("e6-decomposition/split-witness-full", seed)
        assert experiments.histories(R) == experiments.histories(F)


def test_e7_four_fates():
    fates = {}
    for path, goal in [("e1-loop/while-do", "exit"), ("e7-fates/sqrt2-digits", "goal"),
                       ("e4-demand/cycle", "result"), ("e7-fates/goldbach", "goal")]:
        system, C = by_agenda(path)
        window = next((s["max_admissions"] for s in system.plan if s.get("max_admissions")), system.admission_limit)
        terminal = sum(1 for e in C if e["coord"]["kind"] == "exec") < window
        established = goal in experiments.histories(C)
        fates[path] = (established, terminal)
    assert fates == {"e1-loop/while-do": (True, True), "e7-fates/sqrt2-digits": (True, False),
                     "e4-demand/cycle": (False, True), "e7-fates/goldbach": (False, False)}
