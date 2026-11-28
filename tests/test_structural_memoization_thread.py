"""The thread of structural memoization (examples/computability/structural-memoization/thread).

regions          reuse only within the region of the funding signature and the declared cut; a case
                 above the bound of the rules has no plan
scaling          the work of a fresh derivation grows with the number of tiers; a reuse does none
scaling-pruned   the same cases under a planner that drops refused plans
governed         certificate, decision of the board, governed change, revalidation across it,
                 refunds and closure in one record

Each test is named after the claim of thread/DESIGN.md that it checks.
"""
import sys
from copy import deepcopy
from functools import cache

import pytest

from conftest import ROOT, quiet
from ztes.model import judge, realize
from ztes.substrate import lookups
from ztes.substrate.replay import verify
from ztes.substrate.store import MemoryStore, read
from ztes.system import workers
from ztes.system.system import System

THREAD = ROOT / "examples" / "computability" / "structural-memoization" / "thread"
NAMES = ("regions", "scaling", "scaling-pruned", "governed")


@cache
def record(name):
    system, store = System(THREAD / name), MemoryStore()
    system.run(store, log=quiet)
    return tuple(read(store))


@cache
def library():
    lib = {}
    exec((THREAD / "governed" / "lib.py").read_text(), lib)
    return lib


def events(C, abstraction):
    return [e for e in C if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == abstraction]


def payloads(C, *abstractions):
    return [e["payload"] for e in C if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] in abstractions]


def event(C, abstraction, case):
    return next(e for e in events(C, abstraction) if e["payload"].get("case") == case)


def kpi(C):
    return events(C, "kpi")[-1]["payload"]


def judged(prefix, lineage, candidate):
    """The judgment of a candidate by the criterion of the lineage active on the prefix."""
    return judge(list(prefix), lookups.load(prefix, lookups.active(prefix, lineage, "criterion")), candidate)


def proposed(prefix, lineage):
    return realize(list(prefix), lookups.load(prefix, lookups.active(prefix, lineage, "ontology")))


def checker_calls(action, *args):
    """Calls of the checker (proof_error) in the recorded libraries while the action runs."""
    calls = [0]

    def count(frame, kind, arg):
        if kind == "call" and frame.f_code.co_filename == "<library>" and frame.f_code.co_name == "proof_error":
            calls[0] += 1

    previous = sys.getprofile()
    sys.setprofile(count)
    try:
        result = action(*args)
    finally:
        sys.setprofile(previous)
    return result, calls[0]


def test_the_systems_share_their_helpers_and_their_common_specifications():
    shared = THREAD / "governed"
    for name in ("regions", "scaling", "scaling-pruned"):
        assert (THREAD / name / "lib.py").read_text() == (shared / "lib.py").read_text()
        for path in (THREAD / name / "abstractions").rglob("*"):
            if path.is_file() and path.parent.name != "kpi":
                relative = path.relative_to(THREAD / name)
                assert path.read_text() == (shared / relative).read_text(), relative
        for path in (THREAD / name / "abstractions" / "kpi").iterdir():
            assert path.read_text() == (THREAD / "regions" / "abstractions" / "kpi" / path.name).read_text()


# ---- the cost of derivation and of reuse ---------------------------------------------------------

def orders(k, pruned):
    """Plans that the search tests for region k: every order of at most k tiers (blind), or the
    extensions of the one plan refused only as short at each level (pruned)."""
    total, product = 0, 1
    for m in range(1, k + 1):
        product *= k - m + 1
        total += k - m + 1 if pruned else product
    return total


@pytest.mark.parametrize("name, pruned", [("scaling", False), ("scaling-pruned", True)])
def test_the_work_of_a_fresh_derivation_is_that_of_the_planner_version(name, pruned):
    C = record(name)
    rows = [(t["case"], t["tiers"], t["origin"], t["tested"], t["proofs"]) for t in kpi(C)["targets"]]
    expected = []
    for k in (2, 3, 4, 5):
        expected += [(f"S{k}", k, "fresh", orders(k, pruned), orders(k, pruned)), (f"T{k}", k, "reuse", 0, 1)]
    assert rows == expected
    assert [t["tested"] for t in kpi(C)["targets"][::2]] == ([3, 6, 10, 15] if pruned else [4, 15, 64, 325])
    assert [p["users"] for p in kpi(C)["patterns"]] == [["T2"], ["T3"], ["T4"], ["T5"]]


@pytest.mark.parametrize("name", ["scaling", "scaling-pruned"])
def test_a_reused_plan_costs_one_proof_in_the_ontology_and_one_in_the_criterion(name):
    C = record(name)
    for e in events(C, "plan"):
        prefix = C[:e["coord"]["n"]]
        omega, proposing = checker_calls(proposed, prefix, "plan")
        verdict, judging = checker_calls(judged, prefix, "plan", e["payload"])
        assert omega == e["payload"] and verdict
        tested = e["payload"]["metrics"]["tested"]
        # fresh: the search proves each tested plan; the criterion repeats the search and proves the graph
        expected = (1, 1) if e["payload"]["origin"] == "reuse" else (tested, tested + 1)
        assert (proposing, judging) == expected, e["payload"]["case"]
        assert e["payload"]["metrics"]["proofs"] == proposing


def test_the_trace_of_a_derived_plan_is_judged_so_its_counts_are_admitted():
    C = record("scaling")
    e = event(C, "plan", "S4")
    prefix = C[:e["coord"]["n"]]
    assert judged(prefix, "plan", e["payload"])
    shorter = deepcopy(e["payload"])
    shorter["trace"] = shorter["trace"][-1:]
    shorter["metrics"]["tested"] = shorter["metrics"]["proofs"] = 1
    assert not judged(prefix, "plan", shorter)
    fewer = deepcopy(e["payload"])
    fewer["metrics"]["tested"] -= 1
    assert not judged(prefix, "plan", fewer)


# ---- where reuse is sound ------------------------------------------------------------------------

def test_reuse_happens_only_within_the_region_of_the_signature():
    C = record("regions")
    assert [(t["case"], t["region"], t["origin"], t["publication"]) for t in kpi(C)["targets"]] == [
        ("A", 2, "fresh", 0), ("B", 2, "reuse", 1), ("C", 1, "fresh", 0), ("D", 2, "fresh", 0), ("E", 1, "reuse", 2)]
    p1, p2 = payloads(C, "catalogue")
    e = event(C, "plan", "E")
    prefix = C[:e["coord"]["n"]]
    assert judged(prefix, "plan", e["payload"])
    forged = dict(e["payload"], graph=p1["graph"], publication=p1["ordinal"],
                  metrics=dict(e["payload"]["metrics"], inspected=1))
    assert not judged(prefix, "plan", forged)                        # the pattern of another region


def test_what_a_case_may_reuse_is_fixed_by_its_declared_cut():
    C = record("regions")
    d = event(C, "snapshot", "D")
    assert d["payload"]["precedents"] == [] and d["payload"]["visible"] == []
    assert len(payloads(C[:d["coord"]["n"]], "catalogue")) == 2          # P1 exists, but not in the cut
    e = event(C, "plan", "D")
    plan = e["payload"]
    assert plan["origin"] == "fresh" and plan["signature"] == payloads(C, "catalogue")[0]["signature"]
    assert plan["metrics"]["tested"] == 4
    assert [p["case"] for p in payloads(C, "catalogue")] == ["A", "C"]       # no second pattern of P1's kind
    reuse = dict(plan, origin="reuse", publication=1, trace=[],
                 metrics={"expansions": 0, "tested": 0, "proofs": 1, "inspected": 1})
    assert not judged(C[:e["coord"]["n"]], "plan", reuse)


def test_a_case_above_the_bound_has_no_plan_under_the_rules():
    C = record("regions")
    assert event(C, "snapshot", "X") and kpi(C)["waiting"] == ["X"]
    assert all(p["case"] != "X" for p in payloads(C, "plan"))
    assert proposed(C, "plan") is None and proposed(C, "settle") is None


# ---- obstruction and governed change -------------------------------------------------------------

def test_the_certificate_bound_is_the_bound_of_the_settle_criterion():
    C = record("governed")
    plan = event(C, "plan", "X")["payload"]
    settlement = event(C, "settle", "X")["payload"]
    before = C[:event(C, "mandate", "X")["coord"]["n"]]
    assert not judged(before, "plan", plan) and not judged(before, "settle", settlement)
    assert settlement["credit"] == 110 and event(C, "certificate", "X")["payload"]["bound"] == 100
    args = (payloads(C, "funding"), payloads(C, "transport", "cold_chain"), payloads(C, "policy"), [plan], [])
    valid = library()["settlement_valid"]
    assert not valid(settlement, *args, 2) and valid(settlement, *args, 3)


def test_only_the_authority_named_in_the_contract_decides_and_only_on_a_certificate():
    C = record("governed")
    e = event(C, "board", "X")
    assert e["payload"]["issuer"] == event(C, "funding", "X")["payload"]["authority"] == "review-board"
    assert judged(C[:e["coord"]["n"]], "board", e["payload"])
    assert not judged(C[:e["coord"]["n"]], "board", dict(e["payload"], issuer="carrier/X"))
    assert not judged(C[:event(C, "certificate", "X")["coord"]["n"]], "board", e["payload"])


def test_the_mandate_needs_a_certificate_a_decision_and_enough_tiers():
    C = record("governed")
    e = event(C, "mandate", "X")
    candidate, n = e["payload"], e["coord"]["n"]
    assert judged(C[:n], "mandate", candidate)
    assert not judged(C[:event(C, "board", "X")["coord"]["n"]], "mandate", candidate)
    assert not judged(C[:event(C, "certificate", "X")["coord"]["n"]], "mandate", candidate)
    fewer = deepcopy(candidate)
    for s in fewer["specifications"]:
        s["constants"]["K"] = 2
    assert not judged(C[:n], "mandate", fewer)
    partial = dict(candidate, specifications=[s for s in candidate["specifications"] if s["abstraction"] == "plan"])
    assert not judged(C[:n], "mandate", partial)


def test_the_rules_change_once_and_the_certified_case_is_paid_in_full_under_the_new_rules():
    C = record("governed")
    n = {a: event(C, a, "X")["coord"]["n"] for a in ("snapshot", "certificate", "board", "mandate", "plan", "settle")}
    fees = [e["coord"]["n"] for e in events(C, "fee")]
    assert n["snapshot"] < n["certificate"] < n["board"] < n["mandate"] < n["plan"] < n["settle"]
    assert max(fees) < n["mandate"] and len(events(C, "mandate")) == 1
    before = lookups.active(C[:n["mandate"]], "plan", "criterion")
    after = lookups.active(C[:n["mandate"] + 1], "plan", "criterion")
    assert before != after
    judged_by = {e["payload"]["case"]: e["coord"]["criterion"] for e in events(C, "plan")}
    assert judged_by == {"A": before, "B": before, "C": before, "D": before, "E": before,
                         "X": after, "F": after, "G": after, "H": after}
    assert event(C, "settle", "X")["payload"]["draws"] == [60, 40, 10]       # Corollary 9


def test_a_pattern_of_the_earlier_rules_crosses_the_change_only_by_a_new_proof():
    C = record("governed")
    patterns = payloads(C, "catalogue")
    assert [(p["case"], p["versions"]["rules"], p["origin"], p["revalidates"]) for p in patterns] == [
        ("A", "r1", "fresh", 0), ("C", "r1", "fresh", 0), ("X", "r2", "fresh", 0), ("F", "r2", "revalidated", 1)]
    e = event(C, "plan", "F")
    f = e["payload"]
    assert (f["origin"], f["publication"], f["graph"], f["versions"]["rules"]) == (
        "revalidated", 1, patterns[0]["graph"], "r2")
    _, proving = checker_calls(proposed, C[:e["coord"]["n"]], "plan")
    _, judging = checker_calls(judged, C[:e["coord"]["n"]], "plan", f)
    assert (f["metrics"]["proofs"], proving, judging) == (1, 1, 1)
    # G reuses the revalidated pattern; citing P1 itself as a reuse under r2 is refused
    g = event(C, "plan", "G")
    prefix = C[:g["coord"]["n"]]
    assert g["payload"]["publication"] == 4 and judged(prefix, "plan", g["payload"])
    cites_p1 = dict(g["payload"], publication=1, metrics=dict(g["payload"]["metrics"], inspected=1))
    assert not judged(prefix, "plan", cites_p1)
    assert not judged(prefix, "plan", dict(cites_p1, versions=patterns[0]["versions"]))
    assert [(t["case"], t["origin"], t["publication"]) for t in kpi(C)["targets"][-2:]] == [
        ("G", "reuse", 4), ("H", "reuse", 3)]


def test_a_revalidation_is_refused_for_another_signature_or_a_graph_the_checker_refuses():
    C = record("governed")
    e = event(C, "plan", "F")
    prefix, f = C[:e["coord"]["n"]], e["payload"]
    p2 = payloads(C, "catalogue")[1]
    assert not judged(prefix, "plan", dict(f, publication=p2["ordinal"], graph=p2["graph"]))
    lib = library()
    context = (payloads(prefix, "funding"), payloads(prefix, "transport", "cold_chain"),
               payloads(prefix, "snapshot"))
    catalogue, prior = payloads(prefix, "catalogue"), payloads(prefix, "plan")
    assert lib["plan_valid"](f, *context, catalogue, prior, 3, "r2", "breadth-first:v1")
    wrong = lib["graph_of"]([2, 1])
    assert lib["proof_error"](f["signature"], wrong) == "priority"
    forged = deepcopy(catalogue)
    forged[0]["graph"] = wrong
    assert not lib["plan_valid"](dict(f, graph=wrong), *context, forged, prior, 3, "r2", "breadth-first:v1")


# ---- compensation --------------------------------------------------------------------------------

def test_closure_needs_a_refund_for_every_affected_party():
    C = record("governed")
    refunds = events(C, "refund")
    assert [(r["payload"]["actor"], r["payload"]["debits"], r["payload"]["amount"]) for r in refunds] == [
        ("buyer/X", ["fee/2"], 3), ("carrier/X", ["fee/1", "fee/3"], 6)]
    closure = event(C, "closure", "X")
    partial = C[:refunds[1]["coord"]["n"]]
    assert not judged(partial, "closure", closure["payload"]) and verify(list(partial)) == []
    assert judged(C[:closure["coord"]["n"]], "closure", closure["payload"])
    assert closure["payload"]["amount"] == sum(p["amount"] for p in payloads(C, "fee")) == 9


# ---- schedules -----------------------------------------------------------------------------------

def histories(C):
    out = {}
    for e in C:
        c = e["coord"]
        if c["kind"] == "exec" and c["abstraction"] not in ("profile", "kpi"):
            out.setdefault(c["abstraction"], []).append((e["payload"], c["criterion"], c["ontology"]))
    return out


@pytest.mark.parametrize("name", NAMES)
def test_every_abstraction_has_the_history_of_the_agenda_under_workers(name):
    system, store = System(THREAD / name), MemoryStore()
    workers.run(system, store, log=quiet)
    C = list(read(store))
    assert len(C) == len(record(name)) and histories(C) == histories(record(name))
