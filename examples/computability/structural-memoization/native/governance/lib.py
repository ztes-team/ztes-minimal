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
