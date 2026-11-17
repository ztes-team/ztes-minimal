"""Specifications carried by a candidate (substrate/governance.py, docs/specifications-in-execution.md).

A small system: `count` records k = 0, 1, … up to LIMIT, each after `steer` has recorded its decision
for k; `steer` records a decision at every step, and its candidate carries specifications in the
field `specifications`. At step 3 it carries version 2 of the ontology of `count`; at step 4 the
criterion and the ontology of a new abstraction, `late`, which records once, after `count` has
finished. The criterion of `steer` is the authority: it may change the ontology of `count` and bring
in `late`, nothing else.
"""
import copy
import itertools
import random
import time

import pytest

from conftest import make_system, quiet
from ztes.defects import relink
from ztes.substrate import events, governance, lookups
from ztes.substrate.replay import verify
from ztes.substrate.store import MemoryStore, read
from ztes.system import workers

COUNT = {"record": {"k": "integer", "by": "integer"}}
DECISION = {"record": {"r": "integer", "specifications": {"list": "specification"}}}
POLICY = ("w['r'] == steers and counted >= steers and all((s['abstraction'] == 'count' and s['role'] == 'ontology')"
          " or s['abstraction'] == 'late' for s in w['specifications'])")
LATE_CONTEXT = {"n": {"from": "late", "select": "count"}, "counted": {"from": "count", "select": "count"}}
LATE_CRITERION = {"abstraction": "late", "role": "criterion", "version": 1, "returns": "boolean", "total": True,
                  "inputs": {"context": LATE_CONTEXT, "candidate": {"name": "w", "type": "integer"}},
                  "body": {"result": "n == 0 and w == counted"}}
LATE_ONTOLOGY = {"abstraction": "late", "role": "ontology", "version": 1, "partial": True, "returns": "integer",
                 "requires": {"count": 6}, "inputs": {"context": LATE_CONTEXT}, "body": {"result": "None if n else counted"}}


def files(change, new):
    return {
        "count/criterion.v1.json": {"inputs": {"context": ["k"], "candidate": {"name": "w", "type": "Count"}},
                                    "body": {"result": "w['k'] == k and k < LIMIT"}},
        "count/ontology.v1.json": {"inputs": {"context": ["k", "decided"]}, "returns": "Count",
                                   "body": {"result": "None if k >= LIMIT or decided <= k else {'k': k, 'by': 1}"}},
        "steer/criterion.v1.json": {"inputs": {"context": ["steers", "counted"], "candidate": {"name": "w", "type": "Decision"}},
                                    "body": {"result": POLICY}},
        "steer/ontology.v1.json": {"inputs": {"context": ["steers", "counted"]}, "returns": "Decision",
                                   "body": {"result": "None if steers >= LIMIT or counted < steers else "
                                                      "{'r': steers, 'specifications': CHANGE if steers == 3 else (NEW if steers == 4 else [])}"}},
    }


def definition(change, new):
    return {"system": "steered", "abstractions": ["count", "steer"],
            "types": {"Count": COUNT, "Decision": DECISION},
            "constants": {"LIMIT": 6, "CHANGE": change, "NEW": new},
            "bindings": {"k": {"from": "$self", "select": "count"}, "steers": {"from": "$self", "select": "count"},
                         "decided": {"from": "steer", "select": "count"}, "counted": {"from": "count", "select": "count"}}}


_PLAIN = itertools.count()


def count_v2(tmp_path, version=2, body="None if k >= LIMIT or decided <= k else {'k': k, 'by': 2}"):
    """Version 2 of the ontology of count, complete: the expanded version 1 with another body."""
    plain = make_system(tmp_path / f"plain-{next(_PLAIN)}", definition([], []), files([], []))
    s = copy.deepcopy(plain.specs["count/ontology.v1"])
    s["version"], s["body"] = version, {"result": body}
    return s


def steered(tmp_path, change=None, new=None):
    change = [count_v2(tmp_path)] if change is None else change
    new = [LATE_CRITERION, LATE_ONTOLOGY] if new is None else new
    return make_system(tmp_path / "steered", definition(change, new), files(change, new))


def by_agenda(system):
    store = MemoryStore()
    system.run(store, log=quiet)
    return list(read(store))


def values(C, a):
    return [e["payload"] for e in C if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == a]


def lineages(C):
    out = {}
    for e in C:
        if e["coord"]["kind"] == "exec":
            out.setdefault(e["coord"]["abstraction"], []).append(e["payload"])
    return out


def test_a_carried_ontology_is_active_from_its_event_and_replays(tmp_path):
    system = steered(tmp_path)
    C = by_agenda(system)
    assert [x["by"] for x in values(C, "count")] == [1, 1, 1, 2, 2, 2]
    n = next(k for k, e in enumerate(C) if e["coord"].get("carries") and e["payload"]["r"] == 3)
    carried = C[n]["coord"]["carries"]
    assert carried["field"] == "specifications" and [(d["abstraction"], d["role"], d["version"]) for d in carried["specs"]] == [("count", "ontology", 2)]
    assert lookups.active(C[:n], "count", "ontology") != carried["specs"][0]["addr"]
    assert lookups.active(C[:n + 1], "count", "ontology") == carried["specs"][0]["addr"]   # active from its event on
    bound = C[n]["payload"]["specifications"][0]
    assert bound["criterion"] == lookups.active(C[:n], "count", "criterion")               # bound by Z₀, as in phase 2
    assert sum(1 for e in C if e["coord"].get("carries")) == 2                             # an empty decision carries nothing
    assert all("carries" not in e["coord"] for e in C if e["coord"]["kind"] == "exec"
               and not (isinstance(e["payload"], dict) and e["payload"].get("specifications")))
    assert verify(C) == [] and verify(C, judgments_only=True) == []


def test_a_criterion_and_its_ontology_carried_together_bring_in_a_new_abstraction(tmp_path):
    system = steered(tmp_path)
    C = by_agenda(system)
    assert values(C, "late") == [6]                                                      # after count has finished
    assert system.abstractions == ["count", "steer", "late"]
    assert system.states(C) == {"count": "wait", "steer": "wait", "late": "wait"}
    late = next(e for e in C if e["coord"].get("abstraction") == "late")
    assert late["coord"]["criterion"] == lookups.active(C, "late", "criterion")
    again = by_agenda(system)                                                             # a second run starts as declared
    assert again == C and system.abstractions == ["count", "steer", "late"]


@pytest.mark.parametrize("case", ["policy", "gap", "no criterion"])
def test_a_refused_candidate_leaves_the_record_unchanged(tmp_path, case):
    """The proposer's criterion refuses a change it may not make (the criterion of count); τ_root
    refuses a version with a gap, and an ontology of a new abstraction carried without its criterion.
    Either way the decision is not recorded: steer is closed, and count waits for it."""
    if case == "policy":
        plain = make_system(tmp_path / "plain", definition([], []), files([], []))
        c2 = copy.deepcopy(plain.specs["count/criterion.v1"])
        c2["version"] = 2
        system, at = steered(tmp_path, change=[c2]), 3
    elif case == "gap":
        system, at = steered(tmp_path, change=[count_v2(tmp_path, version=3)]), 3
    else:
        system, at = steered(tmp_path, new=[LATE_ONTOLOGY]), 4
    C = by_agenda(system)
    assert [x["r"] for x in values(C, "steer")] == list(range(at))
    assert len(values(C, "count")) == at and "late" not in lineages(C)
    assert system.states(C)["steer"] == "closed" and verify(C) == []


def test_an_interrupted_run_continues_to_the_same_record(tmp_path):
    system = steered(tmp_path)
    full = by_agenda(system)
    carrying = [k for k, e in enumerate(full) if e["coord"].get("carries")]
    for cut in sorted({1, carrying[0], carrying[0] + 1, carrying[1] + 1, len(full) - 1, len(full)}):
        store = MemoryStore()
        for n in range(cut):
            store.put_if_absent(n, copy.deepcopy(full[n]))
        system.run(store, log=quiet)
        assert list(read(store)) == full, f"interrupted after {cut} events"


def test_the_same_histories_by_workers_under_random_schedules(tmp_path):
    """The decision pattern of the design (§4): steer decides at every step, count waits for it, late
    waits for count. Every lineage then has the history of the agenda, and the worker of late is
    started by the coordinator when the decision that brings it in is appended."""
    system = steered(tmp_path)
    expected = lineages(by_agenda(system))
    for seed in range(4):
        rnd = random.Random(seed)
        store = MemoryStore()
        workers.run(system, store, log=quiet, hesitate=lambda: time.sleep(rnd.random() * 0.002))
        C = list(read(store))
        assert verify(C) == [] and lineages(C) == expected
        assert system.states(C) == {"count": "wait", "steer": "wait", "late": "wait"}


def test_a_carried_specification_altered_in_the_record_fails_replay(tmp_path):
    C = by_agenda(steered(tmp_path))
    n = next(k for k, e in enumerate(C) if e["coord"].get("carries"))
    body = copy.deepcopy(C)                                  # another body, the coordinate as it was
    body[n]["payload"]["specifications"][0]["body"] = {"result": "None"}
    body = relink(body)
    assert verify(body)[0][0] == n
    assert verify(body, judgments_only=True)[0] == (n, "S1.3 the coordinate does not list what the payload carries")
    gap = copy.deepcopy(C)                                   # a version with a gap, in the payload and the coordinate
    gap[n]["payload"]["specifications"][0]["version"] = 3
    gap[n]["coord"]["carries"]["specs"][0].update(version=3, addr=events.addr(gap[n]["payload"]["specifications"][0]))
    gap = relink(gap)
    first = verify(gap, judgments_only=True)[0]
    assert first[0] == n and "carried specification not admissible" in first[1] and "the next version of count/ontology is 2" in first[1]
    lineage = copy.deepcopy(C)                               # bound to another criterion, consistently
    lineage[n]["payload"]["specifications"][0]["criterion"] = "0" * 64
    lineage[n]["coord"]["carries"]["specs"][0]["addr"] = events.addr(lineage[n]["payload"]["specifications"][0])
    lineage = relink(lineage)
    for mode in (False, True):
        first = verify(lineage, judgments_only=mode)[0]
        assert first[0] == n and ("lineage: bound to criterion " + "0" * 64 in first[1] or not mode)


# ---- τ_root on what a candidate carries (governance.carry) ----

def test_tau_root_judges_the_carried_specifications_in_order(tmp_path):
    system = steered(tmp_path, change=[], new=[])
    C = by_agenda(system)                                       # nothing carried: the record of v1
    o = lookups.load(C, lookups.active(C, "steer", "ontology"))
    crit = lookups.active(C, "count", "criterion")
    v2, v3 = count_v2(tmp_path), count_v2(tmp_path, version=3)
    c2 = dict(system.specs["count/criterion.v1"], version=2)

    def carry(*specs):
        w = {"r": 0, "specifications": list(specs)}
        before = copy.deepcopy(w)
        out = governance.carry(C, o, w)
        assert w == before                                      # the candidate given is not changed
        return out

    assert governance.carry(C, o, {"r": 0, "specifications": []}) == ({"r": 0, "specifications": []}, None, None)
    w, carries, why = carry(v2)
    assert why is None and w["specifications"][0]["criterion"] == crit
    assert carries == {"field": "specifications", "specs": [{"abstraction": "count", "role": "ontology", "version": 2,
                                                             "addr": events.addr(w["specifications"][0])}]}
    w, carries, why = carry(dict(v2, criterion="0" * 64))      # Z₀ binds it, whatever the proposer wrote
    assert why is None and w["specifications"][0]["criterion"] == crit
    w, carries, why = carry(c2, v2)                             # bound to the criterion carried before it
    assert why is None and w["specifications"][1]["criterion"] == events.addr(c2) != crit
    assert carry(v2, v3)[2] is None                             # two versions of one lineage, in order
    assert carry(v2, v2)[2] == "carried specification 1: version 2: the next version of count/ontology is 3"
    assert carry(v3)[2] == "carried specification 0: version 3: the next version of count/ontology is 2"
    assert carry(LATE_ONTOLOGY, LATE_CRITERION)[2] == \
        "carried specification 0: no criterion of late is recorded or carried before it"
    assert carry(LATE_CRITERION, LATE_ONTOLOGY)[2] is None
    assert carry(v2, {"abstraction": "count", "role": "ontology"})[2].startswith("carried specification 1: ")
    for bad in ({}, {"abstraction": ["count"], "role": "ontology"}, {"abstraction": {"a": 1}, "role": "criterion"},
                {"abstraction": "count", "role": ["ontology"]}, dict(v2, version="2"), dict(v2, abstraction=7)):
        assert carry(bad)[2].startswith("carried specification 0: "), bad   # refused, never an error of Z₀
    assert carry(v2, LATE_ONTOLOGY)[1] is None                  # refused: nothing to list in a coordinate
    count = lookups.load(C, lookups.active(C, "count", "ontology"))
    assert governance.carry(C, count, {"k": 0, "by": 1}) == ({"k": 0, "by": 1}, None, None)   # no carried field


def test_tau_root_refuses_an_ontology_with_two_carried_fields(tmp_path):
    C = by_agenda(steered(tmp_path, change=[], new=[]))
    s = dict(lookups.load(C, lookups.active(C, "steer", "ontology")), version=2)
    assert governance.refusal(C, s) is None
    s["returns"] = {"record": {"r": "integer", "specifications": {"list": "specification"},
                               "more": {"list": "specification"}}}
    assert "not more" in governance.refusal(C, s)


# ---- an abstraction that does not read the proposer (idle) ----

def idle_system(tmp_path, requires=True):
    """idle records 0 and 1 and waits; steer, once idle has two events (or at once, without
    `requires`), carries version 2 of the ontology of idle, which goes on to 3. idle reads only
    itself: nothing but the specification carried for it makes it run again."""
    def build(change, root):
        steer = {"inputs": {"context": ["steers"]}, "returns": "Decision",
                 "body": {"result": "None if steers else {'r': 0, 'specifications': CHANGE}"}}
        if requires:
            steer["requires"], steer["inputs"]["context"] = {"idle": 2}, ["steers", "idles"]
        return make_system(root, {
            "system": "idle", "abstractions": ["idle", "steer"], "types": {"Decision": DECISION},
            "constants": {"CHANGE": change},
            "bindings": {"k": {"from": "$self", "select": "count"}, "steers": {"from": "$self", "select": "count"},
                         "idles": {"from": "idle", "select": "count"}},
        }, {
            "idle/criterion.v1.json": {"inputs": {"context": ["k"], "candidate": {"name": "w", "type": "integer"}},
                                       "body": {"result": "w == k"}},
            "idle/ontology.v1.json": {"inputs": {"context": ["k"]}, "returns": "integer",
                                      "body": {"result": "None if k >= 2 else k"}},
            "steer/criterion.v1.json": {"inputs": {"context": ["steers"], "candidate": {"name": "w", "type": "Decision"}},
                                        "body": {"result": "w['r'] == steers"}},
            "steer/ontology.v1.json": steer,
        })
    v2 = copy.deepcopy(build([], tmp_path / "plain").specs["idle/ontology.v1"])
    v2["version"], v2["body"] = 2, {"result": "None if k >= 4 else k"}
    return build([v2], tmp_path / "idle"), v2


def test_an_abstraction_whose_specification_is_carried_is_evaluated_again(tmp_path):
    system, _ = idle_system(tmp_path)
    C = by_agenda(system)
    assert values(C, "idle") == [0, 1, 2, 3] and verify(C) == []
    for seed in range(4):                                       # a waiting worker is due again
        rnd = random.Random(seed)
        store = MemoryStore()
        workers.run(system, store, log=quiet, hesitate=lambda: time.sleep(rnd.random() * 0.002))
        D = list(read(store))
        assert verify(D) == [] and values(D, "idle") == [0, 1, 2, 3]


def test_a_carried_specification_changes_what_stands(tmp_path):
    """Z₀ appends a candidate on a longer prefix without computing it again only if nothing it
    depends on has changed (Z0._stands): an event carrying a specification of the abstraction counts."""
    system, _ = idle_system(tmp_path)
    store = MemoryStore()
    z0 = system.run(store, log=quiet)
    C = list(read(store))
    n = next(k for k, e in enumerate(C) if e["coord"].get("carries"))
    assert not z0._stands(C[:n], C[:n + 1], "idle")
    plain = copy.deepcopy(C[n])
    del plain["coord"]["carries"]                               # the same event, carrying nothing
    assert z0._stands(C[:n], C[:n] + [plain], "idle")


class Racing(MemoryStore):
    """A store where another instance of Z₀ appends `event(C)` first, when Z₀ next appends."""

    event = None

    def put_if_absent(self, n, e):
        if self.event is not None:
            other, self.event = self.event(list(read(self))), None
            super().put_if_absent(n, other)
            return False
        return super().put_if_absent(n, e)


def test_a_carrying_candidate_is_judged_again_after_a_race(tmp_path):
    """steer reads only itself, so a governed change of idle appended first leaves its candidate as
    it was; but the version it carries is now taken, and τ_root must judge it again."""
    system, v2 = idle_system(tmp_path, requires=False)
    store = Racing()
    z0 = system.run(store, log=quiet, plan=[{"phase": 1}, {"phase": 2}])

    def governed(C):
        return events.spec_event(C, dict(v2, criterion=lookups.active(C, "idle", "criterion")))

    store.event = governed
    assert z0.execute("steer")[0] == "false"
    C = list(read(store))
    assert C[-1]["coord"]["kind"] == "spec" and verify(C) == []


# ---- the run around it: KPI, coordinator, command line ----

def test_the_profile_counts_the_abstractions_of_its_criterion(tmp_path):
    """The first profile is recorded for the abstractions of the system at that time; one adopted
    later is not counted by it (kpi.observation)."""
    system = steered(tmp_path)
    store = MemoryStore()
    system.run(store, log=quiet, plan=[{"phase": 1}, {"phase": 2}, {"phase": 3}, {"kpi": True}])
    C = list(read(store))
    assert [x["abstraction"] for x in values(C, "profile")[-1]] == ["count", "steer", "late"]
    assert values(C, "profile")[-1][2]["A"] == 1 and verify(C) == []
    store = MemoryStore()
    system.run(store, log=quiet, plan=[{"phase": 1}, {"phase": 2}, {"phase": 3, "max_admissions": 2},
                                       {"kpi": True}, {"phase": 3}, {"kpi": True}])
    C = list(read(store))
    assert [[x["abstraction"] for x in p] for p in values(C, "profile")] == [["count", "steer"]] * 2
    assert values(C, "late") == [6] and verify(C) == []


def test_a_coordinator_adopts_what_is_carried_and_starts_its_worker(tmp_path):
    system = steered(tmp_path)
    store = MemoryStore()
    for n, e in enumerate(by_agenda(system)):
        store.put_if_absent(n, e)
    started = []
    system.abstractions = list(system.declared)
    workers.Coordinator(store, start=started.append)._adopt(system)
    assert started == ["late"] and system.abstractions == ["count", "steer", "late"]
    system.abstractions = list(system.declared)
    workers.Coordinator(store)._adopt(system)                   # workers elsewhere: adopted, none started here
    assert system.abstractions == ["count", "steer", "late"]


def test_the_command_line_runs_and_verifies_a_record_with_carried_specifications(tmp_path, capsys):
    from ztes.__main__ import main
    system = steered(tmp_path)
    assert system.check(log=quiet) == []
    rec = tmp_path / "rec"
    assert main(["run", str(system.path), "--record", str(rec)]) == 0
    assert main(["verify", str(rec)]) == 0 and main(["verify", str(rec), "--judgments"]) == 0
    out = capsys.readouterr().out
    assert "R2  replay of 18 events: OK" in out and "R2  replay of 18 events (judgments only" in out
    C = by_agenda(system)
    n = next(k for k, e in enumerate(C) if e["coord"].get("carries"))
    assert main(["explain", str(rec), str(n)]) == 0


# ---- carried specifications written as files (authoring: {"$specifications": […]}) ----

def test_a_constant_may_name_the_specification_files_it_carries(tmp_path):
    """The same system with version 2 of count written as a file and named by the constant CHANGE:
    the record is the one of the complete specification written into the constant."""
    fs = files([], [])
    fs["count/ontology.v2.json"] = {"inputs": {"context": ["k", "decided"]}, "returns": "Count",
                                    "body": {"result": "None if k >= LIMIT or decided <= k else {'k': k, 'by': 2}"}}
    d = definition([], [LATE_CRITERION, LATE_ONTOLOGY])
    d["constants"]["CHANGE"] = {"$specifications": ["count/ontology.v2"]}
    named = make_system(tmp_path / "named", d, fs)
    assert named.specs["steer/ontology.v1"]["constants"]["CHANGE"] == [named.specs["count/ontology.v2"]]
    assert by_agenda(named) == by_agenda(steered(tmp_path))


@pytest.mark.parametrize("change, message", [
    ({"$specifications": ["count/ontology.v9"]}, "not a specification file of the system"),
    ({"$specifications": ["count/ontology.v2"], "more": 1}, "alone in its object"),
    ({"$specifications": ["steer/ontology.v2"]}, "names specification files in turn"),
])
def test_a_reference_to_specification_files_is_checked(tmp_path, change, message):
    fs = files([], [])
    fs["count/ontology.v2.json"] = fs["count/ontology.v1.json"]
    fs["steer/ontology.v2.json"] = dict(fs["steer/ontology.v1.json"], constants={"X": {"$specifications": ["count/ontology.v2"]}})
    d = definition([], [])
    d["constants"]["CHANGE"] = change
    with pytest.raises(AssertionError, match=message):
        make_system(tmp_path / "bad", d, fs)
