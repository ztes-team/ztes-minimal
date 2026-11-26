"""ztes.substrate: the record, Z₀, τ_root and R2 replay."""
import json
from pathlib import Path

import pytest

from conftest import FACTOR, SQRT2, make_system, quiet
from ztes.system.system import System
from ztes.substrate.store import DiskStore, RedisStore, read
from ztes.substrate.z0 import ADMITTED, FALSE, NOT_YET, Z0
from ztes.substrate.replay import verify


def test_phase2_requires_phase1(system, tmp_path):
    """τ_root refuses an ontology before its criterion is recorded (§3.1.2)."""
    store = DiskStore(tmp_path)
    k = Z0(store, system.services(store))
    s = dict(system.specs["lower/ontology.v1"], criterion=None)
    assert k.admit_ontology(s) == FALSE
    assert len(read(store)) == 1                       # only genesis


def test_tampering_is_detected(system, tmp_path):
    """A value changed outside Z₀ breaks R2 at that event and the link of the next (Theorem C′)."""
    store = DiskStore(tmp_path)
    system.run(store, log=quiet)
    e = store.get(6)
    e["payload"] = "13/10"                             # still a valid lower bound of √2, but not what was computed
    store.c.set("C|6", e)                           # writes past Axiom 0 (only possible in a test)
    errors = dict(verify(read(DiskStore(tmp_path), check=False)))   # a fresh reader, as `verify DIR` would be
    assert "realization" in errors[6]
    assert "hash link" in errors[7]
    from ztes.substrate import CorruptRecord
    with pytest.raises(CorruptRecord, match="event 7"):   # execution does not continue on a broken chain
        read(DiskStore(tmp_path))


def test_concurrent_substrates_do_not_fork(tmp_path):
    """Two instances of Z₀ judge on the same Cⁿ; only one append at n succeeds, the other re-judges on Cⁿ⁺¹."""
    system = System(SQRT2)
    system.plan = [{"phase": 1}, {"phase": 2}]
    store = DiskStore(tmp_path)
    z1 = system.run(store, log=quiet)
    z2 = Z0(store, system.services(store))

    class Racing:                                      # instance 2 writes between the judgment of instance 1 and its append
        def __init__(self, inner):
            self.inner, self.fired = inner, False

        def get(self, n):
            return self.inner.get(n)

        def put_if_absent(self, n, ev):
            if not self.fired:
                self.fired = True
                assert z2.execute("upper") == (ADMITTED, "3/2")
            return self.inner.put_if_absent(n, ev)

    z1.store = Racing(store)
    result, _ = z1.execute("upper")                    # judged 3/2 on C⁵, lost position 5, re-judged on C⁶
    C = read(store)
    assert [e["payload"] for e in C if e["coord"]["kind"] == "exec"] == ["3/2"]
    assert result == NOT_YET                           # on C⁶ the midpoint 5/4 belongs to lower
    assert verify(C) == []


def test_redis_backend(system):
    import fakeredis
    store = RedisStore(client=fakeredis.FakeRedis())
    system.run(store, log=quiet)
    assert verify(read(store)) == []


def test_tau_root_checks_the_api(system, tmp_path):
    """Malformed specifications are refused when recorded, not when executed."""
    from ztes.substrate.governance import tau_root
    store = DiskStore(tmp_path)
    Z0(store, system.services(store))
    C = read(store)
    good = system.specs["lower/criterion.v1"]
    assert tau_root(C, good)
    bad_select = json.loads(json.dumps(good))
    bad_select["inputs"]["context"]["lower"]["select"] = "median"
    no_default = json.loads(json.dumps(good))
    del no_default["inputs"]["context"]["lower"]["default"]       # τ would not be total
    bad_type = json.loads(json.dumps(good))
    bad_type["inputs"]["candidate"]["type"] = "real"
    assert not any(tau_root(C, s) for s in (bad_select, no_default, bad_type))


def test_tau_root_checks_function_bodies(tmp_path):
    from ztes.substrate.governance import tau_root
    system = System(FACTOR)
    store = DiskStore(tmp_path)
    k = Z0(store, system.services(store))
    k.admit_criterion(system.specs["factor/criterion.v1"])
    C = read(store)
    s = dict(system.specs["factor/ontology.v1"], criterion=C[-1]["coord"]["addr"])
    assert isinstance(s["body"], str) and tau_root(C, s)
    assert not tau_root(C, dict(s, body=s["body"].replace("def omega(n, primes, prev):", "def omega(n, primes, prev, extra):")))
    assert not tau_root(C, dict(s, body=s["body"].replace("for q in primes:", "while True:")))


def test_tau_root_refuses_a_map_that_reads_another_binding(tmp_path):
    from ztes.substrate.governance import tau_root
    s = {"abstraction": "a", "role": "criterion", "version": 1, "returns": "boolean", "total": True,
         "inputs": {"context": {"k": {"from": "a", "select": "count"},
                                "m": {"from": "a", "select": "map", "key": "x + k"}},
                    "candidate": {"name": "w", "type": "integer"}},
         "body": {"result": "True"}}
    assert not tau_root([], s)                                # the map would depend on k: not cacheable
    s["inputs"]["context"]["m"]["key"] = "x"
    assert tau_root([], s)


def test_index_gives_the_same_answers_as_a_plain_list(tmp_path):
    from ztes.substrate import lookups
    store = DiskStore(tmp_path)
    System(Path(__file__).parent.parent / "examples" / "payment").run(store, log=quiet)
    C = read(store)                                     # a Record with a shared index
    plain = list(C)                                     # a plain list: the index is built on demand
    for n in range(len(C) + 1):
        for a in ("requests", "fraud_check", "override", "transfer"):
            for role in ("criterion", "ontology"):
                assert lookups.active(C[:n], a, role) == lookups.active(plain[:n], a, role)
    assert verify(C) == verify(plain) == []


def test_large_record_is_linear(tmp_path):
    """2,000 admissions of two interacting abstractions: run and replay stay well under a few seconds."""
    import time
    system = make_system(tmp_path, {
        "system": "ticks", "abstractions": ["tick", "sum"], "constants": {"N": 1000},
        "bindings": {"k": {"from": "$self", "select": "count"},
                     "t": {"from": "tick", "select": "last", "type": "integer", "default": 0},
                     "s": {"from": "sum", "select": "last", "type": "integer", "default": 0},
                     "ns": {"from": "sum", "select": "count"}}}, {
        "tick/criterion.v1.json": {"inputs": {"context": ["k"], "candidate": {"name": "w", "type": "integer"}},
                                   "body": {"result": "w == k + 1 and w <= N"}},
        "tick/ontology.v1.json": {"inputs": {"context": ["k"]}, "returns": "integer", "body": {"result": "k + 1"}},
        "sum/criterion.v1.json": {"inputs": {"context": ["t", "ns", "s"], "candidate": {"name": "w", "type": "integer"}},
                                  "body": {"result": "ns < t and w == s + t"}},
        "sum/ontology.v1.json": {"inputs": {"context": ["t", "s"]}, "returns": "integer", "body": {"result": "s + t"}},
    })
    from ztes.substrate.store import MemoryStore
    store = MemoryStore()
    t0 = time.time()
    system.run(store, log=quiet)
    C = read(store)
    assert len(C) == 2005 and verify(C) == []
    assert C[-1]["payload"] == 1000 * 1001 // 2
    assert time.time() - t0 < 10


def test_refusal_names_the_reason(system, tmp_path):
    from ztes.substrate.governance import refusal
    store = DiskStore(tmp_path)
    Z0(store, system.services(store))
    C = read(store)
    assert refusal(C, system.specs["lower/criterion.v1"]) is None
    assert "next version of lower/criterion is 1" in refusal(C, system.specs["lower/criterion.v2"])
    o = dict(system.specs["lower/ontology.v1"], criterion="0123456789abcdef" * 4)
    assert "phase 2 requires phase 1" in refusal(C, o)


def test_a_service_reads_its_prefix_without_the_store(system):
    """Z₀ has read Cⁿ; the service evaluating on Cⁿ is served from the cache, with no access to the store."""
    from ztes.substrate.store import MemoryStore
    store = MemoryStore()
    system.run(store, log=quiet)
    n = len(read(store))
    calls = []
    original = store.get
    store.get = lambda k: calls.append(k) or original(k)
    assert len(read(store, n - 3)) == n - 3 and calls == []
    read(store)
    assert calls == [n]                                          # only the check for a new event


def test_kpi_profile_records_what_the_record_does_not_keep(system):
    """KPI: ⊥ and τ false leave no event; the profile abstraction records the counts, and C confirms A."""
    from ztes.substrate.store import MemoryStore
    from ztes.system.kpi import table
    store = MemoryStore()
    system.run(store, log=quiet)                                  # the plan of √2 ends with {"kpi": true}
    C = read(store)
    rows, _ = table(system, C)
    assert (rows["lower"]["I"], rows["lower"]["A"], rows["lower"]["U"], rows["lower"]["F"]) == (5, 3, 1, 1)
    assert (rows["upper"]["I"], rows["upper"]["A"], rows["upper"]["U"], rows["upper"]["F"]) == (5, 3, 2, 0)
    assert rows["lower"]["A"] == sum(1 for e in C if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == "lower")
    assert verify(C) == []


def test_profile_criterion_refuses_an_inconsistent_observation(system):
    """The profile is a boundary occurrence, but its criterion checks all that C can confirm."""
    from ztes.substrate.store import MemoryStore
    from ztes.substrate.z0 import FALSE
    store = MemoryStore()
    z0 = system.run(store, log=quiet)
    good = [{"abstraction": "lower", "I": 6, "A": 3, "U": 2, "H": 0, "F": 1}, {"abstraction": "upper", "I": 6, "A": 3, "U": 3, "H": 0, "F": 0}]
    wrong_a = [dict(good[0], A=4, I=7), good[1]]                   # A does not match the events in C
    wrong_sum = [dict(good[0], U=5), good[1]]                      # I ≠ A + U + F
    fewer = [dict(good[0], I=1, A=3, U=0, F=0) | {"I": 3}, good[1]]  # counts may not decrease
    wrong_h = [dict(good[0], H=3), good[1]]                        # H is a part of U
    for occurrence in (wrong_a, wrong_sum, fewer, wrong_h):
        assert z0.execute("profile", occurrence)[0] == FALSE
    assert z0.execute("profile", good)[0] == ADMITTED


def test_tampering_with_a_profile_is_detected(system):
    """R2 replays the judgment of a boundary occurrence: a changed U breaks I = A + U + F."""
    from ztes.model.view import Record
    from ztes.substrate.store import MemoryStore
    store = MemoryStore()
    system.run(store, log=quiet)
    events = [json.loads(json.dumps(store.c[k])) for k in sorted(store.c)]
    n = next(e["coord"]["n"] for e in events if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == "profile")
    events[n]["payload"][0]["U"] += 1
    errors = dict(verify(Record.of(events)))
    assert "criterion is false" in errors[n]


def test_each_of_the_eight_deviations_is_found_by_replay():
    """Theorem C on the ant colony: the sound record replays; each defective mechanism is stopped."""
    from ztes import defects
    from ztes.substrate.replay import verify
    _, C = defects.run("aco")
    assert verify(C) == []
    expected = ["realization gives", "criterion version not active", "realization gives None",
                "specification address", "ontology version not active", "realization gives",
                "criterion is false on replay", "criterion version not active"]
    found = defects.report(log=lambda *_: None)
    assert len(found) == 8
    for (condition, lost, first), reason in zip(found, expected):
        assert first is not None and reason in first[1], (condition, first)
    assert [lost for _, lost, _ in found] == ["R2", "R1", "S1.2", "R2", "R1", "R2", "R2", "R1"]


def test_lossy_evidence_fails_on_the_stored_candidate_too():
    """Case 6 without re-deriving: the criterion re-judged on what was stored is false."""
    from ztes import defects
    from ztes.model import judge
    from ztes.substrate import lookups
    C = defects.lossy_evidence()
    n = defects.position(C, "tour", 0)
    assert not judge(C[:n], lookups.load(C[:n], C[n]["coord"]["criterion"]), C[n]["payload"])
