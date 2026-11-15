"""Running systems: plans, the agenda and termination, checks, the authoring form, expect, the Python API."""
import json
import shutil

import pytest

from conftest import COUNTER, SQRT2, make_system, quiet
from ztes.system.system import System
from ztes.model import SpecError
from ztes.substrate.store import DiskStore, MemoryStore, read
from ztes.substrate.replay import verify


def test_plan_runs_and_replays(system, tmp_path):
    store = DiskStore(tmp_path)
    system.run(store, log=quiet)
    C = read(store)
    assert verify(C) == []
    values = [e["payload"] for e in C if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] in ("lower", "upper")]
    assert values == ["3/2", "5/4", "11/8", "23/16", "45/32", "91/64"]


def test_sqrt2_termination_states(system, tmp_path):
    store = DiskStore(tmp_path)
    system.run(store, log=quiet)
    assert system.agenda == []                         # Terminal_r(C)
    assert system.states(read(store)) == {"lower": "closed", "upper": "wait"}


def test_generic_context_and_external_wait(tmp_path):
    """count, all + where, record types; an abstraction reading an external lineage waits permanently."""
    system = System(COUNTER)
    store = DiskStore(tmp_path)
    system.run(store, log=quiet)
    C = read(store)
    assert verify(C) == []
    ticks = [e["payload"] for e in C if e["coord"].get("abstraction") == "tick" and e["coord"]["kind"] == "exec"]
    evens = [e["payload"] for e in C if e["coord"].get("abstraction") == "evens" and e["coord"]["kind"] == "exec"]
    assert ticks == [1, 2, 3, 4, 5]
    assert evens == [{"count": 1, "sum": 2}, {"count": 2, "sum": 6}]
    assert system.states(C) == {"tick": "closed", "evens": "closed", "alarm": "wait-external"}


def test_malformed_system_is_refused(tmp_path):
    bad = tmp_path / "bad"
    shutil.copytree(SQRT2, bad)
    f = bad / "abstractions" / "lower" / "criterion.v1.json"
    s = json.loads(f.read_text())
    s["version"] = 3                                   # does not match the file name
    f.write_text(json.dumps(s))
    with pytest.raises(AssertionError, match="must match the file name"):
        System(bad)


def test_check_accepts_the_shipped_systems():
    assert System(SQRT2).check(log=quiet) == []
    assert System(COUNTER).check(log=quiet) == []


def test_check_finds_problems(tmp_path):
    """An undeclared name, a govern step without a file, and a criterion refused by τ_root."""
    bad = tmp_path / "bad"
    shutil.copytree(SQRT2, bad)
    f = bad / "abstractions" / "upper" / "ontology.v1.json"
    s = json.loads(f.read_text())
    s["body"]["m"] = "(lower + top) / 2"                          # 'top' is not declared
    f.write_text(json.dumps(s))
    f = bad / "abstractions" / "lower" / "criterion.v2.json"
    s = json.loads(f.read_text())
    s["returns"] = "rational"                                     # a criterion must return boolean
    f.write_text(json.dumps(s))
    m = json.loads((bad / "system.json").read_text())
    m["plan"].append({"govern": ["upper/ontology.v2"]})           # no such file
    (bad / "system.json").write_text(json.dumps(m))
    problems = "\n".join(System(bad).check(log=quiet))
    assert "undeclared ['top']" in problems
    assert "lower/criterion.v2: a criterion returns \"boolean\"" in problems          # the reason, not only the refusal
    assert "upper/ontology.v2, which has no file" in problems


def test_authoring_format_is_expanded(tmp_path):
    """Identity from the path, named types and bindings, $self, list context, used constants only."""
    system = make_system(tmp_path, {
        "system": "t", "abstractions": ["a"],
        "types": {"Pair": {"record": {"x": "integer", "y": "integer"}}},
        "constants": {"LIMIT": 3, "UNUSED": 9},
        "bindings": {"k": {"from": "$self", "select": "count"}},
    }, {
        "a/criterion.v1.json": {"inputs": {"context": ["k"], "candidate": {"name": "w", "type": "Pair"}},
                                "body": {"result": "w['x'] == k and w['x'] < LIMIT"}},
        "a/ontology.v1.json": {"inputs": {"context": ["k"]}, "returns": "Pair",
                               "body": {"result": "{'x': k, 'y': k * k}"}},
    })
    c = system.specs["a/criterion.v1"]
    assert (c["abstraction"], c["role"], c["version"], c["returns"], c["total"]) == ("a", "criterion", 1, "boolean", True)
    assert c["inputs"]["context"]["k"] == {"from": "a", "select": "count"}
    assert c["inputs"]["candidate"]["type"] == {"record": {"x": "integer", "y": "integer"}}
    assert c["constants"] == {"LIMIT": 3}
    assert system.check(log=quiet) == []
    store = DiskStore(tmp_path / "rec")
    system.run(store, log=quiet)
    C = read(store)
    assert [e["payload"] for e in C if e["coord"]["kind"] == "exec"] == [{"x": 0, "y": 0}, {"x": 1, "y": 1}, {"x": 2, "y": 4}]
    assert verify(C) == []
    assert all("constants" in e["payload"] for e in C if e["coord"]["kind"] == "spec" and e["coord"]["role"] == "criterion")


def test_expect_reports_differences(tmp_path):
    from ztes.system.report import check_expect
    system = System(SQRT2)
    store = DiskStore(tmp_path)
    system.run(store, log=quiet)
    C = read(store)
    assert check_expect(system, C, log=quiet) == []
    system.expect = {"events": 14, "states": {"lower": "wait"}, "values": {"upper": ["3/2"]}}
    assert len(check_expect(system, C, log=quiet)) == 3


def test_python_api_from_dict_and_save(tmp_path):
    """A system built in code runs like one read from a directory, and can be stored in the standard form."""
    from ztes.substrate.store import MemoryStore
    definition = {
        "system": "squares", "abstractions": ["sq"], "constants": {"N": 5},
        "bindings": {"k": {"from": "$self", "select": "count"}},
        "expect": {"events": 8, "states": {"sq": "closed"}, "values": {"sq": [0, 1, 4, 9, 16]}},
        "specifications": {
            "sq/criterion.v1": {"inputs": {"context": ["k"], "candidate": {"name": "w", "type": "integer"}},
                                "body": {"result": "k < N and w == k * k"}},
            "sq/ontology.v1": {"inputs": {"context": ["k"]}, "returns": "integer",
                               "body": "def omega(k):\n    return k * k\n"},
        },
    }
    from ztes.system.report import check_expect
    system = System.from_dict(definition)
    assert system.check(log=quiet) == []
    store = MemoryStore()
    system.run(store, log=quiet)
    assert check_expect(system, read(store), log=quiet) == []
    saved = system.save(tmp_path / "squares", design="# squares\n")
    assert (tmp_path / "squares" / "abstractions" / "sq" / "ontology.v1.json").exists()
    assert saved.specs == system.specs
    assert saved.check(log=quiet) == []


def test_notes_are_for_the_reader_only(tmp_path):
    """A "note" in a specification, a binding or the candidate is removed before recording."""
    plain = make_system(tmp_path / "a", {"system": "n", "abstractions": ["t"],
                                         "bindings": {"k": {"from": "$self", "select": "count"}}}, {
        "t/criterion.v1.json": {"inputs": {"context": ["k"], "candidate": {"name": "w", "type": "integer"}},
                                "body": {"result": "w == k + 1 and w <= 3"}},
        "t/ontology.v1.json": {"inputs": {"context": ["k"]}, "returns": "integer", "body": {"result": "k + 1"}}})
    noted = make_system(tmp_path / "b", {"system": "n", "abstractions": ["t"],
                                         "bindings": {"k": {"from": "$self", "select": "count", "note": "how many"}}}, {
        "t/criterion.v1.json": {"note": "admits 1, 2, 3",
                                "inputs": {"context": ["k"], "candidate": {"name": "w", "type": "integer", "note": "ω"}},
                                "body": {"result": "w == k + 1 and w <= 3"}},
        "t/ontology.v1.json": {"note": "the next number", "inputs": {"context": ["k"]}, "returns": "integer",
                               "body": {"result": "k + 1"}}})
    assert noted.specs == plain.specs


@pytest.mark.parametrize("name", ["sqrt2", "dedekind-cut", "prime-witnesses", "tsp-bnb", "aco", "aco-draw"])
def test_an_interrupted_run_continues_to_the_same_record(name):
    """The process may die after any event: started again, the plan gives the record it would have given.

    The state of the scheduler (agenda, sources, counts of Not Yet and false) is not in C; it is
    walked again from the plan and the record (resume.py), and nothing already recorded is rewritten.
    """
    import copy
    from pathlib import Path
    from ztes.substrate.store import MemoryStore, read
    path = Path(__file__).parent.parent / "examples" / name
    whole = MemoryStore()
    System(path).run(whole, log=quiet)
    full = list(read(whole))
    for cut in (1, 2, 5, len(full) // 2, len(full) - 3, len(full)):
        store = MemoryStore()
        for n in range(cut):
            store.put_if_absent(n, copy.deepcopy(full[n]))
        System(path).run(store, log=quiet)
        assert list(read(store)) == full, f"{name}: interrupted after {cut} events"


def test_a_record_of_another_system_is_not_continued():
    from pathlib import Path
    from ztes.substrate.store import MemoryStore, read
    from ztes.system.resume import DifferentRecord
    examples = Path(__file__).parent.parent / "examples"
    store = MemoryStore()
    System(examples / "sqrt2").run(store, log=quiet)
    n = len(read(store))
    with pytest.raises(DifferentRecord, match="event 1 of the record"):
        System(examples / "payment").run(store, log=quiet)
    assert len(read(store)) == n                               # nothing was appended


def _requiring(tmp_path, ontology):
    """src records 0, 1, 2; once has one result, computed from the three events of src."""
    return make_system(tmp_path, {
        "system": "r", "abstractions": ["once", "src"],
        "constants": {"NEED": 3},
        "bindings": {"k": {"from": "src", "select": "count"}, "mine": {"from": "$self", "select": "count"}},
    }, {
        "src/criterion.v1.json": {"inputs": {"context": {"n": "mine"}, "candidate": {"name": "w", "type": "integer"}},
                                  "body": {"result": "w == n and w < NEED"}},
        "src/ontology.v1.json": {"inputs": {"context": {"n": "mine"}}, "returns": "integer", "body": {"result": "n"}},
        "once/criterion.v1.json": {"inputs": {"context": ["mine"], "candidate": {"name": "w", "type": "integer"}},
                                   "body": {"result": "mine == 0"}},
        "once/ontology.v1.json": {"inputs": {"context": ["k"]}, "returns": "integer", **ontology},
    })


def test_requires_decides_not_yet_without_evaluating_the_body(tmp_path):
    """The body divides by zero on an incomplete horizon; with "requires" it is never evaluated there."""
    body = {"result": "NEED // (k // NEED)"}
    declared = _requiring(tmp_path / "a", {"requires": {"src": "NEED"}, "body": body})
    assert declared.check(log=quiet) == []
    assert declared.specs["once/ontology.v1"]["constants"] == {"NEED": 3}
    store = MemoryStore()
    declared.run(store, log=quiet)
    payloads = lambda C: [(e["coord"]["abstraction"], e["payload"]) for e in C if e["coord"]["kind"] == "exec"]
    assert verify(read(store)) == [] and ("once", 3) in payloads(read(store))
    assert declared.outcomes["once"]["H"] >= 1 and declared.outcomes["once"]["U"] == declared.outcomes["once"]["H"]

    in_body = _requiring(tmp_path / "b", {"body": {"result": "None if k < NEED else NEED // (k // NEED)"}})
    other = MemoryStore()
    in_body.run(other, log=quiet)
    assert payloads(read(other)) == payloads(read(store))          # the same results, in the same order
    assert in_body.outcomes["once"]["H"] == 0                      # there every Not Yet was computed
    assert {k: v for k, v in in_body.outcomes["once"].items() if k != "H"} == \
           {k: v for k, v in declared.outcomes["once"].items() if k != "H"}

    with pytest.raises(SpecError, match="ZeroDivisionError"):      # without either, the body is a defect
        _requiring(tmp_path / "c", {"body": body}).run(MemoryStore(), log=quiet)


def test_requires_is_checked_as_part_of_the_specification(tmp_path):
    body = {"result": "k"}
    for requires, message in (({"other": 1}, "outside the horizon"), ({"src": 0}, "not a positive integer"),
                              (["src"], "must be a JSON object")):
        system = _requiring(tmp_path / str(len(message)), {"requires": requires, "body": body})
        assert any(message in p for p in system.check(log=quiet)), message
