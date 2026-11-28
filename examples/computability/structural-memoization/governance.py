"""Case-local R1 activation, obstruction and R1-c on the ordinary ZTES substrate.

The compensation scope is the contract's refundable ledger fees. Every affected fee
has a reversible ledger posting. Closure therefore requires a refund for each actor;
a declaration of non-compensability is outside the authority granted by this contract.
"""

from inspect import getsource

from ztes.substrate import lookups
from ztes.substrate.replay import verify
from ztes.substrate.store import MemoryStore
from ztes.system.system import System


# These pure domain functions are included by source in the specifications that use them.
def credit(order, report, primary, guarantee, guarantees):
    return {"case": order["case"], "claim": report["ref"], "beneficiary": order["beneficiary"],
            "primary": primary, "guarantee": guarantee, "total": primary + guarantee,
            "instrument": guarantees[0]["ref"] if guarantee > 0 and guarantees else ""}


def valid_credit(w, orders, reports, paid, guarantees, sharing):
    if paid or not orders or not reports:
        return False
    order = orders[0]
    report = reports[0]
    primary = min(report["loss"], order["cap"])
    residual = report["loss"] - primary
    if residual > 0 and (not sharing or not guarantees or guarantees[0]["limit"] < residual):
        return False
    return w == credit(order, report, primary, residual, guarantees)


def obstruction(orders, reports, paid):
    if paid or not orders or not reports or reports[0]["loss"] <= orders[0]["cap"]:
        return None
    return {"case": orders[0]["case"], "claim": reports[0]["ref"], "regime": "primary-only",
            "fixed_loss": reports[0]["loss"], "max_total": orders[0]["cap"]}


def affected_horizons(order, report, debits):
    actors = sorted(set(d["actor"] for d in debits if d["case"] == order["case"]))
    return [{"actor": a, "order": order["ref"], "inspection": report["ref"],
             "debits": [d for d in debits if d["case"] == order["case"] and d["actor"] == a]}
            for a in actors]


def lawful_transition(w, orders, reports, blocks, mandates, charges, debits, changes, reform):
    if changes or not orders or not reports or not blocks or not mandates or len(charges) != len(debits):
        return False
    if (w["case"] != orders[0]["case"] or w["mandate"] != mandates[0]["ref"]
            or w["obstruction"] != blocks[0] or w["affected"] != affected_horizons(orders[0], reports[0], debits)):
        return False
    specs = w["specifications"]
    if len(specs) != 2 or specs[0] != reform[0]:
        return False
    # Z0 binds the carried ontology to the preceding carried criterion; tau_root checks that field.
    return {k: v for k, v in specs[1].items() if k != "criterion"} == reform[1]


def refund(change, horizon):
    return {"case": change["case"], "mandate": change["mandate"], "actor": horizon["actor"],
            "order": horizon["order"], "inspection": horizon["inspection"],
            "debit_refs": [d["ref"] for d in horizon["debits"]],
            "refund": sum(d["amount"] for d in horizon["debits"])}


def next_refund(changes, refunds):
    if changes:
        for horizon in changes[0]["affected"]:
            if all(r["actor"] != horizon["actor"] for r in refunds):
                return refund(changes[0], horizon)
    return None


def covered(w, changes, refunds, closures):
    if not changes or closures:
        return False
    expected = [refund(changes[0], h) for h in changes[0]["affected"]]
    return (len(refunds) == len(expected) and all(item in refunds for item in expected)
            and w == {"mandate": changes[0]["mandate"], "witnesses": refunds})


def governance_system():
    """Authoring form with full prospective v2 code carried in the reform event."""
    def record(**fields):
        return {"record": fields}

    types = {
        "Order": record(case="text", ref="text", cap="integer", beneficiary="text",
                        inspector="text", authority="text", guarantor="text", fee_issuer="text",
                        fee_parties={"list": "text"}),
        "Report": record(case="text", ref="text", issuer="text", loss="integer"),
        "Charge": record(case="text", ref="text", issuer="text", actor="text", amount="integer"),
        "Guarantee": record(case="text", ref="text", claim="text", issuer="text", limit="integer", beneficiary="text"),
        "Mandate": record(case="text", ref="text", claim="text", issuer="text", action="text"),
        "Credit": record(case="text", claim="text", beneficiary="text", primary="integer",
                         guarantee="integer", total="integer", instrument="text"),
        "Obstruction": record(case="text", claim="text", regime="text", fixed_loss="integer", max_total="integer"),
        "Horizon": record(actor="text", order="text", inspection="text", debits={"list": "Charge"}),
        "Refund": record(case="text", mandate="text", actor="text", order="text", inspection="text",
                         debit_refs={"list": "text"}, refund="integer"),
        "Closure": record(mandate="text", witnesses={"list": "Refund"}),
        "Change": record(case="text", mandate="text", obstruction="Obstruction", affected={"list": "Horizon"},
                         specifications={"list": "specification"}),
    }
    lineages = {"orders": "order", "reports": "inspection", "charges": "fee-notice", "debits": "fee-debit",
                "guarantees": "guarantee", "mandates": "mandate", "paid": "case-credit",
                "blocks": "obstruction", "changes": "reform", "refunds": "refund", "closures": "closure"}
    specs = {}

    def abstraction(name, payload, ontology, criterion, omega_context="", tau_context="", version=1):
        candidate = {"name": "w", "type": payload}
        spec = {"inputs": {"context": omega_context.split()}, "returns": payload}
        if ontology is None:
            spec["boundary"] = True
        else:
            spec["body"] = {"result": ontology}
        specs[f"{name}/ontology.v{version}"] = spec
        specs[f"{name}/criterion.v{version}"] = {
            "inputs": {"context": tau_context.split(), "candidate": candidate}, "body": {"result": criterion}}

    abstraction("order", "Order", None,
                "not orders and w['case'] == 'governed-shipment' and w['cap'] >= 0 and "
                "len(w['fee_parties']) == len(set(w['fee_parties'])) and all(w['fee_parties']) and "
                "all(w[k] for k in ('ref','beneficiary','inspector','authority','guarantor','fee_issuer'))",
                tau_context="orders")
    abstraction("inspection", "Report", None,
                "len(orders) == 1 and not reports and w['case'] == orders[0]['case'] and "
                "w['issuer'] == orders[0]['inspector'] and w['loss'] > 0 and w['ref'] != ''",
                tau_context="orders reports")
    abstraction("guarantee", "Guarantee", None,
                "len(orders) == 1 and len(reports) == 1 and not guarantees and w['case'] == orders[0]['case'] and "
                "w['claim'] == reports[0]['ref'] and "
                "w['issuer'] == orders[0]['guarantor'] and w['beneficiary'] == orders[0]['beneficiary'] and "
                "w['limit'] >= 0 and w['ref'] != ''", tau_context="orders reports guarantees")
    abstraction("mandate", "Mandate", None,
                "len(orders) == 1 and len(blocks) == 1 and not mandates and w['case'] == orders[0]['case'] and "
                "w['claim'] == blocks[0]['claim'] and "
                "w['issuer'] == orders[0]['authority'] and w['action'] == 'activate-risk-sharing' and w['ref'] != ''",
                tau_context="orders blocks mandates")
    abstraction("fee-notice", "Charge", None,
                "len(orders) == 1 and not changes and w['case'] == orders[0]['case'] and w['amount'] > 0 "
                "and w['issuer'] == orders[0]['fee_issuer'] and w['actor'] in orders[0]['fee_parties'] "
                "and w['ref'] != '' and all(n['ref'] != w['ref'] for n in charges)",
                tau_context="orders changes charges")
    abstraction("fee-debit", "Charge",
                "charges[len(debits)] if not changes and len(debits) < len(charges) else None",
                "not changes and len(debits) < len(charges) and w == charges[len(debits)]",
                "debits charges changes", "debits charges changes")
    pay_conditions = "valid_credit(w, orders, reports, paid, guarantees, "
    abstraction("case-credit", "Credit",
                "credit(orders[0], reports[0], min(orders[0]['cap'], reports[0]['loss']), 0, []) "
                "if orders and reports and not paid else None", pay_conditions + "False)",
                "orders reports paid", "orders reports paid guarantees")
    abstraction("case-credit", "Credit",
                "credit(orders[0], reports[0], min(orders[0]['cap'], reports[0]['loss']), "
                "max(0, reports[0]['loss'] - orders[0]['cap']), guarantees) if orders and reports and not paid else None",
                pay_conditions + "True)", "orders reports paid guarantees", "orders reports paid guarantees", version=2)
    abstraction("obstruction", "Obstruction", "obstruction(orders, reports, paid) if not blocks and not changes else None",
                "not blocks and not changes and w is not None and w == obstruction(orders, reports, paid)",
                "orders reports paid blocks changes", "orders reports paid blocks changes")
    abstraction("reform", "Change",
                "{'case': orders[0]['case'], 'obstruction': blocks[0], "
                "'mandate': mandates[0]['ref'] if mandates else '', "
                "'affected': affected_horizons(orders[0], reports[0], debits), 'specifications': REFORM} "
                "if orders and reports and blocks and not changes else None",
                "lawful_transition(w, orders, reports, blocks, mandates, charges, debits, changes, REFORM)",
                "orders reports blocks changes mandates debits", "orders reports blocks mandates charges debits changes")
    abstraction("refund", "Refund", "next_refund(changes, refunds)",
                "w is not None and w == next_refund(changes, refunds)", "changes refunds", "changes refunds")
    abstraction("closure", "Closure",
                "{'mandate': changes[0]['mandate'], 'witnesses': refunds} if changes and not closures else None",
                "covered(w, changes, refunds, closures)", "changes refunds closures", "changes refunds closures")
    library = [credit, valid_credit, obstruction, affected_horizons, lawful_transition, refund, next_refund, covered]
    return System.from_dict({
        "system": "governed-shipment", "abstractions": list(lineages.values()), "types": types,
        "library": "\n\n".join(getsource(f) for f in library),
        "bindings": {name: {"from": lineage, "select": "all"} for name, lineage in lineages.items()},
        "constants": {"REFORM": {"$specifications": ["case-credit/criterion.v2", "case-credit/ontology.v2"]}},
        "specifications": specs,
    })


def run_governance():
    """Return a JSON-friendly result and independently replayable experimental records."""
    system = governance_system()
    problems = system.check(log=lambda _: None)
    if problems:
        raise ValueError(problems)
    case = "governed-shipment"
    contract = {"case": case, "ref": "contract-9", "cap": 60, "beneficiary": "receiver",
                "inspector": "surveyor", "authority": "review-board", "guarantor": "mutual",
                "fee_issuer": "fee-office", "fee_parties": ["carrier", "supplier", "warehouse"]}
    report = {"case": case, "ref": "inspection-7", "issuer": "surveyor", "loss": 90}

    def initialized():
        return system.run(MemoryStore(), plan=[{"phase": 1}, {"phase": 2}], log=lambda _: None)

    def step(z0, name, outcome, occurrence=None):
        before = len(z0.prefix())
        actual, value = z0.execute(name, occurrence)
        if actual != outcome or len(z0.prefix()) != before + int(outcome == "admitted"):
            raise AssertionError((name, outcome, actual, value))
        return value

    # A concrete continuation in the same fixed regime witnesses Not Yet for this starting prefix.
    waiting = initialized()
    step(waiting, "order", "admitted", {**contract, "cap": 100})
    step(waiting, "case-credit", "Not Yet")
    wait_n = len(waiting.prefix())
    step(waiting, "inspection", "admitted", report)
    waiting_payment = step(waiting, "case-credit", "admitted")

    governed = initialized()
    step(governed, "order", "admitted", contract)
    step(governed, "inspection", "admitted", report)
    for actor, ref, amount in [("supplier", "fee-1", 4), ("carrier", "fee-2", 2), ("supplier", "fee-3", 3)]:
        step(governed, "fee-notice", "admitted", {"case": case, "actor": actor, "ref": ref,
                                                 "amount": amount, "issuer": contract["fee_issuer"]})
        step(governed, "fee-debit", "admitted")
    rejected_credit = step(governed, "case-credit", "false")
    certificate = step(governed, "obstruction", "admitted")
    step(governed, "inspection", "false", {**report, "loss": 60})
    step(governed, "order", "false", {**contract, "cap": 100})
    step(governed, "mandate", "false", {"case": case, "ref": "bad", "issuer": "supplier", "claim": report["ref"],
                                      "action": "activate-risk-sharing"})
    step(governed, "reform", "false")
    step(governed, "mandate", "admitted", {"case": case, "ref": "mandate-2", "issuer": "review-board", "claim": report["ref"],
                                         "action": "activate-risk-sharing"})
    prior = list(governed.prefix())
    step(governed, "reform", "admitted")
    trigger = governed.prefix()[-1]
    new_addresses = {s["role"]: s["addr"] for s in trigger["coord"]["carries"]["specs"]}
    old_addresses = {role: lookups.active(prior, "case-credit", role) for role in ("criterion", "ontology")}
    if any(old_addresses[r] == a or lookups.active(governed.prefix(), "case-credit", r) != a
           for r, a in new_addresses.items()) or set(new_addresses) != set(old_addresses):
        raise AssertionError("the carried versions did not activate at the governance event")
    step(governed, "case-credit", "false")  # reform alone supplies no guarantee funds
    step(governed, "guarantee", "admitted", {"case": case, "ref": "guarantee-1", "issuer": "mutual", "claim": report["ref"],
                                           "limit": 40, "beneficiary": "receiver"})
    payment = step(governed, "case-credit", "admitted")
    payment_n = len(governed.prefix()) - 1
    step(governed, "case-credit", "Not Yet")  # already posted
    first = step(governed, "refund", "admitted")
    step(governed, "closure", "false")
    partial = list(governed.prefix())
    second = step(governed, "refund", "admitted")
    closure = step(governed, "closure", "admitted")
    if sorted((w["actor"], w["refund"]) for w in closure["witnesses"]) != [("carrier", 2), ("supplier", 7)]:
        raise AssertionError("closure did not cover the actual debits")
    if payment["total"] != report["loss"] or waiting_payment["total"] != report["loss"]:
        raise AssertionError("the continued executions failed to reach the declared full-credit goal")
    records = {"governance_waiting": list(waiting.prefix()), "governance_fixed": prior,
               "governance_incomplete": partial, "governance_complete": list(governed.prefix())}
    replay = {name: verify(record) for name, record in records.items()}
    if any(replay.values()):
        raise AssertionError(replay)
    summary = {
        "case": case, "goal": "beneficiary credited full admitted loss",
        "pending": {"prefix_length": wait_n, "witness": ["inspection", "case-credit"],
                    "same_regime_payment": waiting_payment},
        "obstruction": {"certificate": certificate, "rejected_credit": rejected_credit,
                        "assessment_and_cap_revisions_rejected": True},
        "transition": {"unauthorized_transition_rejected": True, "trigger_event": trigger["coord"]["n"],
                       "governing_criterion": trigger["coord"]["criterion"], "old_versions": old_addresses,
                       "new_versions": new_addresses, "unfunded_payment_rejected": True,
                       "funded_payment_event": payment_n, "funded_payment": payment},
        "compensation": {"scope": "refundable ledger fees posted for contract parties before the trigger",
                         "noncompensability_authorized": False,
                         "prior_actor_horizons": trigger["payload"]["affected"], "refunds": [first, second],
                         "partial_closure_rejected": True, "closure_event": len(governed.prefix()) - 1,
                         "coverage": closure},
        "full_replay_errors": replay,
    }
    return summary, records
