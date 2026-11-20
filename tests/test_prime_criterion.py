"""The optional next-prime criterion under both example horizons."""
from copy import deepcopy

import pytest

from conftest import ROOT, quiet
from ztes import model
from ztes.substrate import events, lookups
from ztes.substrate.replay import verify
from ztes.substrate.store import MemoryStore
from ztes.substrate.z0 import ADMITTED
from ztes.system.system import System

PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23)
SETUP = [{"phase": 1}, {"phase": 2}]
VERSION = "primes/criterion.v2"


@pytest.fixture(params=["prime-witnesses", "factorization"])
def example(request):
    return System(ROOT / "examples" / request.param)


def test_criterion_v2_accepts_exactly_the_next_prime(example):
    core = example.run(MemoryStore(), plan=SETUP, log=quiet)
    initial = core.prefix()
    v1 = lookups.load(initial, lookups.active(initial, "primes", "criterion"))
    assert model.judge(initial, v1, 4) and model.judge(initial, v1, 5)

    assert core.admit_criterion(example.specs[VERSION]) == ADMITTED
    for expected in (*PRIMES, None):
        prefix = core.prefix()
        criterion = lookups.load(prefix, lookups.active(prefix, "primes", "criterion"))
        for candidate in range(-1, 30):
            assert model.judge(prefix, criterion, candidate) == (candidate == expected), (expected, candidate)
        if expected is not None:
            assert core.execute("primes") == (ADMITTED, expected)


def test_admissions_on_each_side_of_the_change_keep_their_evidence(example):
    core = example.run(MemoryStore(), plan=SETUP, log=quiet)
    assert core.execute("primes") == (ADMITTED, 2)
    before = tuple(events.addr(e) for e in core.prefix())
    old_criterion = core.prefix()[-1]["coord"]["criterion"]

    assert core.admit_criterion(example.specs[VERSION]) == ADMITTED
    assert core.execute("primes") == (ADMITTED, 3)
    record = core.prefix()
    assert tuple(events.addr(e) for e in record[:len(before)]) == before
    change = record[len(before)]
    assert change["payload"] == example.specs[VERSION]
    new_criterion = change["coord"]["addr"]
    assert new_criterion != old_criterion
    assert record[-1]["coord"]["criterion"] == new_criterion
    assert verify(record, judgments_only=True) == []
    assert verify(record) == []


def test_governed_prime_stream_can_resume_after_a_gap_in_earlier_certificates(example):
    # This governed ontology can legally admit 5 first under v1. Both 5 and 7
    # are prime, and the old prefix contains no certificate for a divisor of 6.
    definition = deepcopy(example.definition)
    specs = definition["specifications"]
    specs["primes/ontology.v2"] = {**specs["primes/ontology.v1"],
                                   "body": {"result": "5 if p < 5 else 7"}}
    system = System.from_dict(definition)
    plan = [*SETUP, {"govern": ["primes/ontology.v2"]}]
    core = system.run(MemoryStore(), plan=plan, log=quiet)
    assert core.execute("primes") == (ADMITTED, 5)
    original_addresses = tuple(events.addr(e) for e in core.prefix())

    assert core.admit_criterion(system.specs[VERSION]) == ADMITTED
    prefix = core.prefix()
    criterion = lookups.load(prefix, lookups.active(prefix, "primes", "criterion"))
    assert not model.judge(prefix, criterion, 11)  # 7 would be skipped
    assert core.execute("primes") == (ADMITTED, 7)
    record = core.prefix()
    assert tuple(events.addr(e) for e in record[:len(original_addresses)]) == original_addresses
    assert [e["payload"] for e in record if e["coord"]["kind"] == "exec"] == [5, 7]
    assert verify(record, judgments_only=True) == []
    assert verify(record) == []


def test_optional_plan_adds_one_specification_and_preserves_domain_results(example):
    baseline = list(example.run(MemoryStore(), log=quiet).prefix())
    plan = list(example.plan)
    start = next(i for i, step in enumerate(plan) if step.get("phase") == 3)
    plan.insert(start, {"govern": [VERSION]})
    record = list(example.run(MemoryStore(), plan=plan, log=quiet).prefix())

    change = next(i for i, e in enumerate(record)
                  if e["coord"]["kind"] == "spec" and e["payload"] == example.specs[VERSION])
    assert record[:change] == baseline[:change]
    expected_sizes = {"prime-witnesses": (26, 27), "factorization": (27, 28)}
    assert (len(baseline), len(record)) == expected_sizes[example.definition["system"]]

    def admissions(history):
        return [(e["coord"]["abstraction"], e["payload"]) for e in history if e["coord"]["kind"] == "exec"]

    assert admissions(record) == admissions(baseline)
    assert verify(record, judgments_only=True) == []
    assert verify(record) == []
