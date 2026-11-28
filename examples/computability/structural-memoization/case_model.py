"""Specifications and synthetic boundary observations for the supply-dispute experiment.

The constructors at the end of the file serialize the pure functions used by each
role into that role's ZTES specification. The driver supplies observations and
schedules invocations. Execution and replay evaluate the same recorded source.
"""

import inspect
from pathlib import Path

from ztes.model import language
from ztes.substrate.events import addr


def find_case(rows, case):
    for item in rows:
        if item["case"] == case:
            return item
    return None


def base_valid(f):
    return (f["route"] in ["transport", "cold_chain"] and f["priority"] == "primary-first"
            and f["asset"] == f["primary_asset"] == f["supplemental_asset"]
            and min(f["obligation"], f["primary_limit"], f["guarantee_limit"]) >= 0
            and all([f["case"], f["contract"], f["lot"], f["asset"], f["instrument"],
                     f["beneficiary"], f["primary_payer"], f["guarantor"]])
            and len(set([f["beneficiary"], f["primary_payer"], f["guarantor"]])) == 3
            and f["certification"] in ["standard", "independent-review"]
            and f["search_order"] in ["supplemental-first", "primary-first"])


def base_event(f):
    return {"case": f["case"], "ref": "base/" + f["case"], "funding_ref": f["ref"],
            "terms": f, "signature": funding_signature(f["obligation"], f["primary_limit"],
                                                      f["guarantee_limit"]) or []}


def next_base(fundings, prior):
    for f in fundings:
        if base_valid(f) and find_case(prior, f["case"]) is None:
            return base_event(f)
    return None


def evidence_of(evidence, f, kind):
    for e in evidence:
        if e["case"] == f["case"] and e["lot"] == f["lot"] and e["kind"] == kind:
            return e
    return None


def diagnosis_for(base, evidence, route):
    f = base["terms"]
    if f["route"] != route or not base_valid(f):
        return None
    if route == "transport":
        delivery = evidence_of(evidence, f, "delivery")
        inspection = evidence_of(evidence, f, "inspection")
        if (delivery is None or inspection is None or delivery["issuer"] != "carrier"
                or inspection["issuer"] != "inspector" or inspection["finding"] != "damaged"
                or inspection["value"] != f["obligation"]):
            return None
        refs = [delivery["ref"], inspection["ref"]]
    else:
        reading = evidence_of(evidence, f, "temperature")
        calibration = evidence_of(evidence, f, "calibration")
        quality = evidence_of(evidence, f, "quality")
        if (reading is None or calibration is None or quality is None
                or reading["issuer"] != "logger" or reading["value"] <= 8
                or calibration["issuer"] != "metrology" or calibration["finding"] != "valid"
                or not reading["sensor"] or calibration["sensor"] != reading["sensor"]
                or quality["issuer"] != "quality-office" or quality["finding"] != "breach"
                or quality["value"] != f["obligation"]):
            return None
        refs = [reading["ref"], calibration["ref"], quality["ref"]]
    return {"case": f["case"], "ref": route + "/" + f["case"], "route": route,
            "base_ref": base["ref"], "signature": base["signature"], "evidence": refs}


def next_diagnosis(bases, evidence, route, prior):
    for base in bases:
        if find_case(prior, base["case"]) is None:
            diag = diagnosis_for(base, evidence, route)
            if diag is not None:
                return diag
    return None


def snapshot_for(diag, catalogue):
    refs = [p["ordinal"] for p in catalogue]
    return {"case": diag["case"], "ref": f"snapshot/{diag['case']}/{len(refs)}",
            "diag_ref": diag["ref"], "visible": refs}


def next_snapshot(diagnoses, catalogue, prior):
    for diag in diagnoses:
        if find_case(prior, diag["case"]) is None:
            return snapshot_for(diag, catalogue)
    return None


def versions_for(f):
    versions = construction_versions()
    if f["search_order"] == "primary-first":
        versions["planner"] = "breadth-first-primary-first:v2"
    versions["certification"] = f["certification"]
    return versions


def review_ref(f, evidence):
    if f["certification"] == "standard":
        return ""
    review = evidence_of(evidence, f, "review")
    if review is not None and review["issuer"] == "review-panel" and review["finding"] == "approved":
        return review["ref"]
    return None


def make_plan(f, diag, snap, catalogue, evidence):
    signature = diag["signature"]
    review = review_ref(f, evidence)
    if not signature or review is None:
        return None
    versions = versions_for(f)
    trace = []
    skipped = []
    graph = []
    publication = 0
    inspected = 0
    validated = 0
    expansions = 0
    tested = 0
    bindings = 0
    allocation = None
    for p in catalogue:
        if p["ordinal"] not in snap["visible"]:
            continue
        inspected += 1
        if compatible_pattern(p, signature, versions):
            validated += 1
            if verify_graph(signature, p["graph"]):
                bindings += 1
                allocation = bind_graph(p["graph"], f["obligation"], f["primary_limit"], f["guarantee_limit"])
                if allocation is not None:
                    graph = p["graph"]
                    publication = p["ordinal"]
                    break
            skipped.append(p["graph"])
    if not publication:
        search = search_graph_avoiding(signature, skipped, f["search_order"] == "primary-first")
        graph = search["graph"]
        trace = search["trace"]
        expansions = search["expansions"]
        tested = search["tested"]
        if not graph:
            return None
        bindings += 1
        allocation = bind_graph(graph, f["obligation"], f["primary_limit"], f["guarantee_limit"])
        if allocation is None:
            return None
    return {"case": f["case"], "ref": "plan/" + f["case"], "diag_ref": diag["ref"],
            "signature": signature, "versions": versions, "review_ref": review,
            "snapshot_ref": snap["ref"], "graph": graph, "trace": trace,
            "origin": "reuse" if publication else "fresh", "publication": publication,
            "allocation": allocation, "metrics": {"expansions": expansions, "tested": tested,
            "inspected": inspected, "validated": validated, "bindings": bindings}}


def next_plan(fundings, diagnoses, snapshots, catalogue, evidence, prior):
    for snap in snapshots:
        case = snap["case"]
        if find_case(prior, case) is None:
            f = find_case(fundings, case)
            diag = find_case(diagnoses, case)
            if f is not None and diag is not None and diag["ref"] == snap["diag_ref"]:
                plan = make_plan(f, diag, snap, catalogue, evidence)
                if plan is not None:
                    return plan
    return None


def plan_valid(w, fundings, diagnoses, snapshots, catalogue, evidence, prior):
    case = w["case"]
    f = find_case(fundings, case)
    diag = find_case(diagnoses, case)
    snap = find_case(snapshots, case)
    if f is None or diag is None or snap is None or find_case(prior, case) is not None:
        return False
    if (w["ref"] != "plan/" + case or w["diag_ref"] != diag["ref"] or snap["diag_ref"] != diag["ref"]
            or w["snapshot_ref"] != snap["ref"] or w["signature"] != diag["signature"]
            or w["versions"] != versions_for(f) or w["review_ref"] != review_ref(f, evidence)
            or not verify_graph(w["signature"], w["graph"])):
        return False
    allocation = bind_graph(w["graph"], f["obligation"], f["primary_limit"], f["guarantee_limit"])
    if allocation != w["allocation"]:
        return False
    if w["origin"] == "fresh":
        return (w["publication"] == 0 and len(w["trace"]) > 0
                and w["trace"][-1]["graph"] == w["graph"] and w["trace"][-1]["reason"] == "verified")
    if w["origin"] != "reuse" or w["publication"] not in snap["visible"] or w["trace"]:
        return False
    return any(p["ordinal"] == w["publication"] and p["graph"] == w["graph"]
               and compatible_pattern(p, w["signature"], w["versions"]) for p in catalogue)


def settlement_for(f, diag, policy, plan):
    return {"case": f["case"], "ref": "settlement/" + f["case"], "plan_ref": plan["ref"],
            "policy_ref": policy["ref"], "diag_ref": diag["ref"], "evidence": diag["evidence"],
            "contract": f["contract"], "asset": f["asset"], "beneficiary": f["beneficiary"],
            "primary_payer": f["primary_payer"], "guarantor": f["guarantor"],
            "primary": plan["allocation"]["primary"], "supplemental": plan["allocation"]["supplemental"],
            "credit": plan["allocation"]["credit"], "origin": plan["origin"], "publication": plan["publication"]}


def next_settlement(plans, fundings, diagnoses, policies, prior):
    candidate = None
    for plan in plans:
        case = plan["case"]
        if find_case(prior, case) is None:
            f = find_case(fundings, case)
            diag = find_case(diagnoses, case)
            policy = find_case(policies, case)
            if f is not None and diag is not None and policy is not None:
                proposed = settlement_for(f, diag, policy, plan)
                if diag["route"] in policy["covers"]:
                    return proposed
                if candidate is None:
                    candidate = proposed
    return candidate


def settlement_valid(w, fundings, diagnoses, policies, plans, prior):
    case = w["case"]
    f = find_case(fundings, case)
    diag = find_case(diagnoses, case)
    policy = find_case(policies, case)
    plan = find_case(plans, case)
    if f is None or diag is None or policy is None or plan is None or find_case(prior, case) is not None:
        return False
    x = w["primary"]
    y = w["supplemental"]
    return (w == settlement_for(f, diag, policy, plan) and diag["route"] in policy["covers"]
            and policy["contract"] == f["contract"] and policy["asset"] == f["asset"]
            and policy["instrument"] == f["instrument"] and policy["guarantor"] == f["guarantor"]
            and policy["beneficiary"] == f["beneficiary"] and policy["approved"]
            and x == min(f["obligation"], f["primary_limit"]) and 0 <= x <= policy["primary_available"]
            and 0 <= y <= min(f["guarantee_limit"], policy["guarantee_available"])
            and x + y == w["credit"] == f["obligation"])


def published(ordinal, plan, pay):
    return {"ordinal": ordinal, "ref": f"catalogue/{ordinal}", "case": plan["case"],
            "signature": plan["signature"], "versions": plan["versions"], "graph": plan["graph"],
            "diag_ref": plan["diag_ref"], "plan_ref": plan["ref"], "payment_ref": pay["ref"],
            "obligations": ["coverage", "available balances", "beneficiary", "local authority"]}


def next_publication(plans, payments, prior):
    for pay in payments:
        plan = find_case(plans, pay["case"])
        if (plan is not None and plan["origin"] == "fresh" and pay["plan_ref"] == plan["ref"]
                and find_case(prior, pay["case"]) is None):
            return published(len(prior) + 1, plan, pay)
    return None


def publication_valid(w, plans, payments, prior):
    plan = find_case(plans, w["case"])
    pay = find_case(payments, w["case"])
    return (plan is not None and pay is not None and find_case(prior, w["case"]) is None
            and plan["origin"] == "fresh" and pay["plan_ref"] == plan["ref"]
            and w == published(len(prior) + 1, plan, pay) and verify_graph(w["signature"], w["graph"]))


# The following declarations are used only to build recorded specifications and fixtures.
def record(**fields):
    return {"record": fields}


T = "text"
I = "integer"
FLAG = "boolean"
TEXTS = {"list": T}
FUNDING = record(case=T, ref=T, contract=T, lot=T, route=T, asset=T, primary_asset=T,
                 supplemental_asset=T, beneficiary=T, primary_payer=T, guarantor=T, instrument=T,
                 obligation=I, primary_limit=I, guarantee_limit=I, priority=T, certification=T,
                 search_order=T)
POLICY = record(case=T, ref=T, contract=T, instrument=T, asset=T, beneficiary=T, guarantor=T,
                covers=TEXTS, approved=FLAG, primary_available=I, guarantee_available=I)
EVIDENCE = record(case=T, ref=T, lot=T, kind=T, issuer=T, finding=T, sensor=T, value=I)
BASE = record(case=T, ref=T, funding_ref=T, terms=FUNDING, signature=TEXTS)
DIAG = record(case=T, ref=T, route=T, base_ref=T, signature=TEXTS, evidence=TEXTS)
SNAP = record(case=T, ref=T, diag_ref=T, visible={"list": I})
VERSIONS = record(interface=T, reduction=T, planner=T, primitives=T, checker=T, certification=T)
NODE = record(op=T, role=T, inputs=TEXTS, out=T)
GRAPH = {"list": NODE}
ALLOCATION = record(primary=I, supplemental=I, credit=I)
METRICS = record(expansions=I, tested=I, inspected=I, validated=I, bindings=I)
PLAN = record(case=T, ref=T, diag_ref=T, snapshot_ref=T, signature=TEXTS, versions=VERSIONS,
              review_ref=T, graph=GRAPH, trace={"list": record(graph=GRAPH, reason=T)},
              origin=T, publication=I, allocation=ALLOCATION, metrics=METRICS)
PAYMENT = record(case=T, ref=T, plan_ref=T, policy_ref=T, diag_ref=T, evidence=TEXTS,
                 contract=T, asset=T, beneficiary=T, primary_payer=T, guarantor=T,
                 primary=I, supplemental=I, credit=I, origin=T, publication=I)
PUBLICATION = record(ordinal=I, ref=T, case=T, signature=TEXTS, versions=VERSIONS, graph=GRAPH,
                     diag_ref=T, plan_ref=T, payment_ref=T, obligations=TEXTS)


def specifications():
    """Build (criterion, ontology) pairs. Helper source is included transitively by role."""
    planner = Path(__file__).with_name("planner.py").read_text(encoding="utf-8")
    domain = [find_case, base_valid, base_event, next_base, evidence_of, diagnosis_for, next_diagnosis,
              snapshot_for, next_snapshot, versions_for, review_ref, make_plan, next_plan, plan_valid,
              settlement_for, next_settlement, settlement_valid, published, next_publication, publication_valid]
    library = planner + "\n\n" + "\n\n".join(inspect.getsource(fn) for fn in domain)
    bindings = {"fundings": "funding", "policies": "policy", "evidence": "evidence", "bases": "base",
                "diagnoses": ["transport", "cold_chain"], "catalogue": "catalogue", "snapshots": "snapshot",
                "plans": "plan", "payments": "settle"}
    result = []

    def role(name, kind, role_name, expr, names, constants):
        context = {key: {"from": name if key == "prior" else bindings[key], "select": "all", "type": "json"}
                   for key in names.split()}
        spec = {"abstraction": name, "version": 1, "role": role_name, "inputs": {"context": context}}
        if role_name == "criterion":
            spec["inputs"]["candidate"] = {"name": "w", "type": kind}
            spec.update(returns="boolean", total=True)
        else:
            spec.update(returns=kind, partial=True)
        if expr is None:
            spec["boundary"] = True
            return spec
        spec["body"] = {"result": expr}
        if constants:
            spec["constants"] = constants
        helpers = language.library_subset(library, language.free_names(expr))
        if helpers:
            spec["library"] = helpers
        return spec

    def pair(name, kind, ontology, reads, criterion, checks, constants=None):
        tau = role(name, kind, "criterion", criterion, checks, constants)
        omega = role(name, kind, "ontology", ontology, reads, constants)
        omega["criterion"] = addr(tau)
        result.append((tau, omega))

    pair("funding", FUNDING, None, "",
         "base_valid(w) and w['ref'] == 'funding/' + w['case'] and find_case(prior,w['case']) is None", "prior")
    pair("policy", POLICY, None, "",
         "w['ref'] == 'policy/' + w['case'] and w['case'] != '' and min(w['primary_available'], "
         "w['guarantee_available']) >= 0 and find_case(prior,w['case']) is None", "prior")
    pair("evidence", EVIDENCE, None, "",
         "w['ref'] == w['case'] + '/' + w['kind'] and w['kind'] in "
         "['delivery','inspection','temperature','calibration','quality','review'] "
         "and all([w['case'],w['lot'],w['issuer']]) and all(e['ref'] != w['ref'] for e in prior)", "prior")
    pair("base", BASE, "next_base(fundings,prior)", "fundings prior",
         "find_case(prior,w['case']) is None and any(base_valid(f) and w == base_event(f) for f in fundings)",
         "fundings prior")
    for route in ["transport", "cold_chain"]:
        pair(route, DIAG, "next_diagnosis(bases,evidence,ROUTE,prior)", "bases evidence prior",
             "find_case(prior,w['case']) is None and any(w == diagnosis_for(b,evidence,ROUTE) for b in bases)",
             "bases evidence prior", {"ROUTE": route})
    pair("snapshot", SNAP, "next_snapshot(diagnoses,catalogue,prior)", "diagnoses catalogue prior",
         "find_case(prior,w['case']) is None and any(w == snapshot_for(d,catalogue) for d in diagnoses)",
         "diagnoses catalogue prior")
    controls = "fundings diagnoses snapshots catalogue evidence prior"
    pair("plan", PLAN, "next_plan(fundings,diagnoses,snapshots,catalogue,evidence,prior)", controls,
         "plan_valid(w,fundings,diagnoses,snapshots,catalogue,evidence,prior)", controls)
    controls = "plans fundings diagnoses policies prior"
    pair("settle", PAYMENT, "next_settlement(plans,fundings,diagnoses,policies,prior)", controls,
         "settlement_valid(w,fundings,diagnoses,policies,plans,prior)", controls)
    pair("catalogue", PUBLICATION, "next_publication(plans,payments,prior)", "plans payments prior",
         "publication_valid(w,plans,payments,prior)", "plans payments prior")
    return result


def fixture_inputs(case, excluded=False, stricter=False, revised=False):
    """Immutable synthetic business inputs. Scheduler timing controls catalogue availability."""
    if case not in {"A", "B"}:
        raise ValueError("fixture case must be A or B")
    transport = case == "A"
    route = "transport" if transport else "cold_chain"
    due, cap, guarantee = (90, 60, 40) if transport else (65, 45, 30)
    terms = {"case": case, "ref": "funding/" + case, "contract": "order/" + case, "route": route,
             "lot": "lot/" + case, "asset": "settlement-unit", "primary_asset": "settlement-unit",
             "supplemental_asset": "settlement-unit", "priority": "primary-first",
             "primary_payer": "carrier/" + case, "guarantor": "guarantor/" + case,
             "instrument": "instrument/" + case, "beneficiary": "buyer/" + case, "obligation": due,
             "primary_limit": cap, "guarantee_limit": guarantee,
             "certification": "independent-review" if stricter else "standard",
             "search_order": "primary-first" if revised else "supplemental-first"}
    policy = {"case": case, "ref": "policy/" + case, "contract": terms["contract"], "instrument": terms["instrument"],
              "asset": terms["asset"], "beneficiary": terms["beneficiary"], "guarantor": terms["guarantor"],
              "approved": True, "covers": [] if excluded else [route],
              "primary_available": cap, "guarantee_available": guarantee}
    observations = [("delivery", "carrier", "clean", "", 0), ("inspection", "inspector", "damaged", "", due)]
    if not transport:
        observations = [("temperature", "logger", "measured", "device/B", 12),
                        ("calibration", "metrology", "valid", "device/B", 0),
                        ("quality", "quality-office", "breach", "", due)]
    if stricter:
        observations.append(("review", "review-panel", "approved", "", 0))
    events = [("funding", terms), ("policy", policy)]
    for kind, issuer, finding, sensor, value in observations:
        events.append(("evidence", {"case": case, "ref": case + "/" + kind, "lot": terms["lot"],
                     "kind": kind, "issuer": issuer, "finding": finding, "sensor": sensor, "value": value}))
    return events
