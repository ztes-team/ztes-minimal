# Helper functions shared by the specifications of the thread systems (regions, scaling, governed).
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules): a constant
# of the rules (K, RULES, FEES) reaches a helper only as an argument.
#
# A case owes D and has ordered tiers of payment with limits L_1 … L_n (primary, guarantor,
# reserve, …). The rules in force let the first K tiers pay, each only after the tier before it is
# exhausted. The reduced signature of a case is the number of tiers it may use, k = min(K, n), and
# its region j: L_1 + … + L_(j-1) < D ≤ L_1 + … + L_j. A plan is a typed graph of the operations
# allocate, residual and credit; a graph of the language is fixed by the order in which it draws
# on the tiers. The checker proves a graph for the whole region of a signature, not for one case.
# A published pattern carries the versions under which it was derived. A case reads only the
# publications of the precedents that its policy accepts (the declared cut); it reuses a pattern of
# its signature and versions, or checks again under the versions in force one of its signature that
# was derived under others (revalidated), or searches.


# ---- the record --------------------------------------------------------------------------------

def find_case(rows, case):
    for x in rows:
        if x["case"] == case:
            return x
    return None


def parties(f):
    return [f["beneficiary"]] + f["payers"]


def funding_valid(f):
    names = parties(f) + [f["authority"]]
    return (f["route"] in ["transport", "cold_chain"] and f["owed"] > 0 and len(f["limits"]) > 0
            and all(x > 0 for x in f["limits"]) and len(f["payers"]) == len(f["limits"])
            and all(names) and len(set(names)) == len(names) and f["ref"] == "funding/" + f["case"])


def earlier(fundings, case):
    """The cases funded before this one."""
    out = []
    for f in fundings:
        if f["case"] == case:
            return out
        out.append(f["case"])
    return out


def evidence_of(evidence, case, kind):
    for e in evidence:
        if e["case"] == case and e["kind"] == kind:
            return e
    return None


def diagnosis_for(f, evidence, route):
    """Transport needs a damaged inspection; cold chain a temperature breach and a quality breach.
    Both state the loss that the funding of the case owes."""
    if f["route"] != route:
        return None
    c = f["case"]
    if route == "transport":
        x = evidence_of(evidence, c, "inspection")
        if x is None or x["issuer"] != "inspector" or x["finding"] != "damaged" or x["value"] != f["owed"]:
            return None
        refs = [x["ref"]]
    else:
        t = evidence_of(evidence, c, "temperature")
        q = evidence_of(evidence, c, "quality")
        if (t is None or q is None or t["issuer"] != "logger" or t["value"] <= 8
                or q["issuer"] != "quality-office" or q["finding"] != "breach" or q["value"] != f["owed"]):
            return None
        refs = [t["ref"], q["ref"]]
    return {"case": c, "ref": route + "/" + c, "route": route, "funding_ref": f["ref"], "evidence": refs}


def next_diagnosis(fundings, evidence, route, prior):
    for f in fundings:
        if find_case(prior, f["case"]) is None:
            d = diagnosis_for(f, evidence, route)
            if d is not None:
                return d
    return None


def listed(catalogue, signature, versions):
    """Whether the catalogue already holds a pattern of this signature under these versions."""
    return any(p["signature"] == signature and p["versions"] == versions for p in catalogue)


def done(case, plans, settlements, catalogue):
    """A case is done for the catalogue when it is settled and its plan is reused, published, or
    already listed under the same signature and versions (then there is nothing to publish)."""
    p = find_case(plans, case)
    if p is None or find_case(settlements, case) is None:
        return False
    return (p["origin"] == "reuse" or find_case(catalogue, case) is not None
            or listed(catalogue, p["signature"], p["versions"]))


def snapshot_for(d, policy, catalogue):
    """The declared cut: the publications of the precedents that the policy of the case accepts."""
    return {"case": d["case"], "ref": "snapshot/" + d["case"], "diag_ref": d["ref"],
            "precedents": policy["precedents"],
            "visible": [p["ordinal"] for p in catalogue if p["case"] in policy["precedents"]]}


def next_snapshot(fundings, diagnoses, policies, plans, settlements, catalogue, prior):
    """Cases are taken in the order of their fundings. A snapshot waits until every earlier case is
    done, so the cut it declares is the same under every schedule."""
    for f in fundings:
        c = f["case"]
        if find_case(prior, c) is None:
            d = find_case(diagnoses, c)
            policy = find_case(policies, c)
            if d is None or policy is None:
                return None
            return snapshot_for(d, policy, catalogue)
        if not done(c, plans, settlements, catalogue):
            return None
    return None


# ---- reduction, plan language and checker --------------------------------------------------------

def reduction(owed, limits, K):
    k = min(K, len(limits))
    total = 0
    for j in range(1, k + 1):
        if owed <= total + limits[j - 1]:
            return {"tiers": k, "region": j}
        total += limits[j - 1]
    return None


def versions_of(rules, planner):
    return {"rules": rules, "planner": planner, "checker": "cone:v1"}


def allocation_node(t, balance):
    return {"op": "allocate", "tier": t, "inputs": [balance, f"limit{t}"], "out": f"draw{t}"}


def residual_node(t, balance):
    return {"op": "residual", "tier": t, "inputs": [balance, f"draw{t}"], "out": f"after{t}"}


def credit_node(order):
    return {"op": "credit", "tier": 0, "inputs": [f"draw{t}" for t in sorted(order)], "out": "credit"}


def graph_of(order):
    graph = []
    balance = "owed"
    for n in range(len(order)):
        t = order[n]
        graph.append(allocation_node(t, balance))
        if n < len(order) - 1:
            graph.append(residual_node(t, balance))
            balance = f"after{t}"
    graph.append(credit_node(order))
    return graph


def order_of(graph):
    return [x["tier"] for x in graph if x["op"] == "allocate"]


def wiring_error(graph, k):
    order = order_of(graph)
    if not order or len(set(order)) != len(order) or any(t < 1 or t > k for t in order):
        return "wiring"
    if graph != graph_of(order):
        return "wiring"
    return ""


def unit(n, i):
    return [1 if m == i else 0 for m in range(n)]


def plus(x, y):
    return [x[m] + y[m] for m in range(len(x))]


def minus(x, y):
    return [x[m] - y[m] for m in range(len(x))]


def cone_min(x, y):
    """A coefficientwise smaller form is smaller throughout the nonnegative orthant."""
    if all(x[m] <= y[m] for m in range(len(x))):
        return x
    if all(y[m] <= x[m] for m in range(len(x))):
        return y
    return None


def parameter_forms(signature):
    """The obligation and the limits as forms in k + 1 nonnegative parameters, for region j:
    L_1 … L_(j-1), r = D − (L_1 + … + L_(j-1)), h = L_j − r, L_(j+1) … L_k."""
    k = signature["tiers"]
    j = signature["region"]
    forms = {}
    owed = unit(k + 1, j - 1)
    for i in range(1, k + 1):
        if i < j:
            forms[f"limit{i}"] = unit(k + 1, i - 1)
            owed = plus(owed, unit(k + 1, i - 1))
        elif i == j:
            forms[f"limit{i}"] = plus(unit(k + 1, j - 1), unit(k + 1, j))
        else:
            forms[f"limit{i}"] = unit(k + 1, i)
    forms["owed"] = owed
    return forms


def proof_error(signature, graph):
    """Prove a graph for the whole region of its signature; "" if it is proved, else the reason.

    priority    a tier is drawn before every tier above it is exhausted
    undecided   a draw depends on a comparison that the region does not decide
    negative    a balance can be negative in the region
    short       the credit is not the obligation throughout the region
    """
    error = wiring_error(graph, signature["tiers"])
    if error:
        return error
    values = parameter_forms(signature)
    for x in graph:
        a = [values[p] for p in x["inputs"]]
        if x["op"] == "credit":
            total = a[0]
            for y in a[1:]:
                total = plus(total, y)
            if total != values["owed"]:
                return "short"
            return ""
        if x["op"] == "allocate":
            for i in range(1, x["tier"]):
                if values.get(f"draw{i}") != values[f"limit{i}"]:
                    return "priority"
            v = cone_min(a[0], a[1])
            if v is None:
                return "undecided"
        else:
            v = minus(a[0], a[1])
        if min(v) < 0:
            return "negative"
        values[x["out"]] = v
    return "wiring"


def search_plan(signature, planner):
    """Breadth-first over the plans of the language, by the number of tiers drawn; within a level,
    highest tier first. The enumeration order is part of the planner version.

    breadth-first:v1          extends every plan; the rules are only in the checker
    breadth-first-pruned:v1   extends a plan only if the checker refused it as short: a refusal
                              for priority, undecided or negative holds for every extension
    """
    k = signature["tiers"]
    result = {"graph": [], "trace": [], "expansions": 0}
    frontier = [[]]
    for level in range(k):
        following = []
        for partial in frontier:
            result["expansions"] += 1
            for t in range(k, 0, -1):
                if t in partial:
                    continue
                order = partial + [t]
                error = proof_error(signature, graph_of(order))
                result["trace"].append({"order": order, "reason": error or "verified"})
                if not error:
                    result["graph"] = graph_of(order)
                    return result
                if planner != "breadth-first-pruned:v1" or error == "short":
                    following.append(order)
        frontier = following
    return result


def bind(graph, owed, limits):
    """Execute a graph on the amounts of one case: the draw of every tier (0 if not drawn)."""
    if wiring_error(graph, len(limits)):
        return None
    values = {"owed": owed}
    for i in range(len(limits)):
        values[f"limit{i + 1}"] = limits[i]
    for x in graph:
        a = [values[p] for p in x["inputs"]]
        if x["op"] == "allocate":
            v = min(a[0], a[1])
        elif x["op"] == "residual":
            v = a[0] - a[1]
        else:
            v = sum(a)
        if v < 0:
            return None
        values[x["out"]] = v
    if values["credit"] != owed:
        return None
    return [values.get(f"draw{i + 1}", 0) for i in range(len(limits))]


# ---- plan, settlement, catalogue -----------------------------------------------------------------

def plan_record(f, d, snap, signature, versions, graph, trace, origin, publication, draws, expansions, inspected):
    proofs = len(trace) if origin == "fresh" else 1
    return {"case": f["case"], "ref": "plan/" + f["case"], "diag_ref": d["ref"], "snapshot_ref": snap["ref"],
            "signature": signature, "versions": versions, "graph": graph, "trace": trace, "origin": origin,
            "publication": publication, "draws": draws,
            "metrics": {"expansions": expansions, "tested": len(trace), "proofs": proofs, "inspected": inspected}}


def make_plan(f, d, snap, catalogue, K, rules, planner):
    """In the declared cut: reuse the first publication of the same signature and versions; else
    check again, under the versions in force, the first one of the same signature (revalidated);
    else search."""
    signature = reduction(f["owed"], f["limits"], K)
    if signature is None:
        return None
    versions = versions_of(rules, planner)
    visible = [p for p in catalogue if p["ordinal"] in snap["visible"]]
    for n in range(len(visible)):
        p = visible[n]
        if p["signature"] == signature and p["versions"] == versions and proof_error(signature, p["graph"]) == "":
            draws = bind(p["graph"], f["owed"], f["limits"])
            if draws is not None:
                return plan_record(f, d, snap, signature, versions, p["graph"], [], "reuse", p["ordinal"],
                                   draws, 0, n + 1)
    for p in visible:
        if p["signature"] == signature and p["versions"] != versions and proof_error(signature, p["graph"]) == "":
            draws = bind(p["graph"], f["owed"], f["limits"])
            if draws is not None:
                return plan_record(f, d, snap, signature, versions, p["graph"], [], "revalidated", p["ordinal"],
                                   draws, 0, len(visible))
    s = search_plan(signature, planner)
    if not s["graph"]:
        return None
    draws = bind(s["graph"], f["owed"], f["limits"])
    if draws is None:
        return None
    return plan_record(f, d, snap, signature, versions, s["graph"], s["trace"], "fresh", 0, draws,
                       s["expansions"], len(visible))


def next_plan(fundings, diagnoses, snapshots, catalogue, prior, K, rules, planner):
    for snap in snapshots:
        c = snap["case"]
        if find_case(prior, c) is None:
            f = find_case(fundings, c)
            d = find_case(diagnoses, c)
            if f is not None and d is not None and d["ref"] == snap["diag_ref"]:
                p = make_plan(f, d, snap, catalogue, K, rules, planner)
                if p is not None:
                    return p
    return None


def plan_valid(w, fundings, diagnoses, snapshots, catalogue, prior, K, rules, planner):
    """The graph is proved for the signature under the rules in force and binds to the case. A reused
    graph is a visible publication of the same signature and versions; a revalidated one, a visible
    publication of the same signature under other versions, proved again now; a derived one is the
    result of the search, with the plans it tested and why each was refused."""
    c = w["case"]
    f = find_case(fundings, c)
    d = find_case(diagnoses, c)
    snap = find_case(snapshots, c)
    if f is None or d is None or snap is None or find_case(prior, c) is not None:
        return False
    signature = reduction(f["owed"], f["limits"], K)
    versions = versions_of(rules, planner)
    if (signature is None or w["ref"] != "plan/" + c or w["diag_ref"] != d["ref"] or snap["diag_ref"] != d["ref"]
            or w["snapshot_ref"] != snap["ref"] or w["signature"] != signature or w["versions"] != versions
            or proof_error(signature, w["graph"]) != "" or w["draws"] != bind(w["graph"], f["owed"], f["limits"])):
        return False
    visible = [p for p in catalogue if p["ordinal"] in snap["visible"]]
    m = w["metrics"]
    if w["origin"] == "fresh":
        s = search_plan(signature, planner)
        return (w["publication"] == 0 and w["graph"] == s["graph"] and w["trace"] == s["trace"]
                and m == {"expansions": s["expansions"], "tested": len(s["trace"]), "proofs": len(s["trace"]),
                          "inspected": len(visible)})
    if (w["origin"] not in ["reuse", "revalidated"] or len(w["trace"]) > 0 or m["expansions"] != 0
            or m["tested"] != 0 or m["proofs"] != 1):
        return False
    for n in range(len(visible)):
        p = visible[n]
        if p["ordinal"] == w["publication"]:
            if p["signature"] != signature or p["graph"] != w["graph"]:
                return False
            if w["origin"] == "reuse":
                return p["versions"] == versions and m["inspected"] == n + 1
            return p["versions"] != versions and m["inspected"] == len(visible)
    return False


def settlement_for(f, d, policy, plan):
    return {"case": f["case"], "ref": "settlement/" + f["case"], "plan_ref": plan["ref"],
            "policy_ref": policy["ref"], "diag_ref": d["ref"], "beneficiary": f["beneficiary"],
            "payers": f["payers"], "draws": plan["draws"], "credit": sum(plan["draws"]),
            "origin": plan["origin"], "publication": plan["publication"]}


def next_settlement(fundings, diagnoses, policies, plans, prior):
    for plan in plans:
        c = plan["case"]
        if find_case(prior, c) is None:
            f = find_case(fundings, c)
            d = find_case(diagnoses, c)
            policy = find_case(policies, c)
            if f is not None and d is not None and policy is not None:
                return settlement_for(f, d, policy, plan)
    return None


def settlement_valid(w, fundings, diagnoses, policies, plans, prior, K):
    """Local judgment of the target: its own policy covers the diagnosis and the balances; only the
    first K tiers pay, each after the tier before it is exhausted; the credit is the loss."""
    c = w["case"]
    f = find_case(fundings, c)
    d = find_case(diagnoses, c)
    policy = find_case(policies, c)
    plan = find_case(plans, c)
    if f is None or d is None or policy is None or plan is None or find_case(prior, c) is not None:
        return False
    if w != settlement_for(f, d, policy, plan):
        return False
    x = w["draws"]
    n = len(f["limits"])
    return (d["route"] in policy["covers"] and policy["approved"] and len(policy["available"]) == n
            and len(x) == n and all(x[i] == 0 for i in range(K, n))
            and all(0 <= x[i] <= min(f["limits"][i], policy["available"][i]) for i in range(n))
            and all(x[i + 1] == 0 or x[i] == f["limits"][i] for i in range(n - 1))
            and w["credit"] == f["owed"])


def published(n, plan, s):
    return {"ordinal": n, "ref": f"catalogue/{n}", "case": plan["case"], "signature": plan["signature"],
            "versions": plan["versions"], "graph": plan["graph"], "origin": plan["origin"],
            "revalidates": plan["publication"], "plan_ref": plan["ref"], "settlement_ref": s["ref"]}


def publishable(plan, s, prior):
    """A settled plan that was derived or revalidated, of a signature and versions not yet listed."""
    return (plan is not None and s is not None and plan["origin"] in ["fresh", "revalidated"]
            and s["plan_ref"] == plan["ref"] and find_case(prior, plan["case"]) is None
            and not listed(prior, plan["signature"], plan["versions"]))


def next_publication(plans, settlements, prior):
    for s in settlements:
        plan = find_case(plans, s["case"])
        if publishable(plan, s, prior):
            return published(len(prior) + 1, plan, s)
    return None


def publication_valid(w, plans, settlements, prior):
    plan = find_case(plans, w["case"])
    s = find_case(settlements, w["case"])
    return (publishable(plan, s, prior) and w == published(len(prior) + 1, plan, s)
            and proof_error(w["signature"], w["graph"]) == "")


# ---- obstruction, governed change, compensation --------------------------------------------------

def bound_of(f, K):
    return sum(f["limits"][:min(K, len(f["limits"]))])


def certificate_for(f, K, rules):
    return {"case": f["case"], "ref": "certificate/" + f["case"], "rules": rules,
            "bound": bound_of(f, K), "loss": f["owed"]}


def next_certificate(fundings, snapshots, plans, prior, K, rules):
    for f in fundings:
        c = f["case"]
        if (find_case(snapshots, c) is not None and find_case(plans, c) is None and find_case(prior, c) is None
                and reduction(f["owed"], f["limits"], K) is None):
            return certificate_for(f, K, rules)
    return None


def certificate_valid(w, fundings, snapshots, plans, prior, K, rules):
    """Proposition 14: under the rules in force a settlement credits at most the first K limits, and
    the funding of a case is recorded once; a loss above that bound is never credited in full."""
    f = find_case(fundings, w["case"])
    return (f is not None and find_case(snapshots, w["case"]) is not None and find_case(plans, w["case"]) is None
            and find_case(prior, w["case"]) is None and w == certificate_for(f, K, rules) and w["loss"] > w["bound"])


def fees_of(fees, case):
    return [x for x in fees if x["case"] == case]


def affected(fees, case):
    return sorted(set(x["actor"] for x in fees if x["case"] == case))


def refund_for(m, actor, fees):
    debits = [x for x in fees if x["case"] == m["case"] and x["actor"] == actor]
    return {"case": m["case"], "ref": "refund/" + actor, "mandate": m["ref"], "actor": actor,
            "debits": [x["ref"] for x in debits], "amount": sum(x["amount"] for x in debits)}


def refunded(refunds, case, actor):
    return any(r["case"] == case and r["actor"] == actor for r in refunds)


def next_refund(mandates, fees, prior):
    for m in mandates:
        for a in affected(fees, m["case"]):
            if not refunded(prior, m["case"], a):
                return refund_for(m, a, fees)
    return None


def closure_for(m, refunds):
    rs = [r for r in refunds if r["case"] == m["case"]]
    return {"case": m["case"], "ref": "closure/" + m["case"], "mandate": m["ref"],
            "refunds": [r["ref"] for r in rs], "amount": sum(r["amount"] for r in rs)}


def covered(m, fees, refunds):
    return all(refunded(refunds, m["case"], a) for a in affected(fees, m["case"]))


# ---- indicators ----------------------------------------------------------------------------------

def measure(snapshots, plans, catalogue):
    targets = [{"case": p["case"], "rules": p["versions"]["rules"], "tiers": p["signature"]["tiers"],
                "region": p["signature"]["region"], "origin": p["origin"], "publication": p["publication"],
                "tested": p["metrics"]["tested"], "expansions": p["metrics"]["expansions"],
                "proofs": p["metrics"]["proofs"], "inspected": p["metrics"]["inspected"]} for p in plans]
    patterns = [{"ordinal": x["ordinal"], "case": x["case"], "rules": x["versions"]["rules"],
                 "tiers": x["signature"]["tiers"], "region": x["signature"]["region"], "origin": x["origin"],
                 "revalidates": x["revalidates"],
                 "users": [p["case"] for p in plans if p["origin"] == "reuse" and p["publication"] == x["ordinal"]]}
                for x in catalogue]
    waiting = [s["case"] for s in snapshots if find_case(plans, s["case"]) is None]
    return {"targets": targets, "patterns": patterns, "waiting": waiting}
