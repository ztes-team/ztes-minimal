# Pure helper definitions embedded in the admitted ZTES specifications.


def split_signature():
    return [
        "funding:v1", "recognized-obligation", "primary-first",
        "nominated-supplemental", "compatible-units", "0<S<D<=S+G",
    ]


def funding_signature(d, s, g):
    """Reduction on admitted diagnoses whose amounts and local asset have been validated."""
    if 0 < s < d <= s + g:
        return split_signature()
    return None


def construction_versions():
    return {
        "interface": "funding:v1", "reduction": "funding-reduction:v1",
        "planner": "breadth-first:v1", "primitives": "funding-primitives:v1",
        "checker": "cone:v1",
    }


def compatible_pattern(publication, signature, versions):
    return (signature == split_signature() and publication.get("signature") == signature
            and publication.get("versions") == versions)


def allocation_node(role, balance):
    return {"op": "allocate", "role": role, "inputs": [balance, role + "_limit"],
            "out": role + "_draw"}


def residual_node(role, balance):
    return {"op": "residual", "role": role, "inputs": [balance, role + "_draw"],
            "out": "after_" + role}


def credit_node(roles):
    ports = [role + "_draw" for role in ["primary", "supplemental"] if role in roles]
    return {"op": "credit", "role": "beneficiary", "inputs": ports, "out": "credit"}


def wiring_error(graph):
    """Check ports in definition order and require each allocation to feed the credit."""
    if not graph or len(graph) > 4:
        return "a closed graph needs between one and four nodes"
    roles = []
    balance = "owed"
    unused_draw = ""
    for i in range(len(graph)):
        node = graph[i]
        op = node.get("op")
        role = node.get("role")
        if op == "allocate":
            if role not in ["primary", "supplemental"] or role in roles or unused_draw:
                return "an allocation needs a fresh role and the current obligation"
            if node != allocation_node(role, balance):
                return "allocation ports or role limit do not match"
            roles.append(role)
            unused_draw = role
        elif op == "residual":
            if len(roles) != 1 or role != unused_draw or node != residual_node(role, balance):
                return "residual must consume the outstanding obligation and its draw"
            balance = node["out"]
            unused_draw = ""
        elif op == "credit":
            if not unused_draw or i != len(graph) - 1 or node != credit_node(roles):
                return "terminal credit must cite every allocation exactly once"
            return ""
        else:
            return "unrecognized operation"
    return "missing terminal credit"


def cone_min(left, right):
    """A coefficientwise smaller form is smaller throughout the nonnegative orthant."""
    if all(left[i] <= right[i] for i in range(3)):
        return left
    if all(right[i] <= left[i] for i in range(3)):
        return right
    return None


def proof_error(signature, graph):
    """Check a graph symbolically on the whole signature using S, r=D-S, h=G-r.

    Each value is an affine homogeneous form in these three nonnegative parameters.
    A minimum of incomparable forms has no uniform branch in this checker.
    """
    if signature != split_signature():
        return "unsupported signature"
    error = wiring_error(graph)
    if error:
        return error
    values = {"owed": [1, 1, 0], "primary_limit": [1, 0, 0],
              "supplemental_limit": [0, 1, 1]}
    for node in graph:
        ports = node["inputs"]
        if node["op"] == "credit":
            total = [sum(values[port][i] for port in ports) for i in range(3)]
            if total != values["owed"]:
                return "credit does not cover the obligation throughout the signature"
            if values.get("primary_draw") != values["primary_limit"]:
                return "priority requires exhaustion of the primary limit"
            return ""
        left, right = values[ports[0]], values[ports[1]]
        if node["op"] == "allocate":
            value = cone_min(left, right)
            if value is None:
                return "draw depends on an unresolved comparison in the signature"
        else:
            value = [left[i] - right[i] for i in range(3)]
        if min(value) < 0:
            return "nonnegativity cannot be proved throughout the signature"
        values[node["out"]] = value
    return "missing proof of credit"


def verify_graph(signature, graph):
    """Independent of the search procedure and of the source case's numeric bindings."""
    return proof_error(signature, graph) == ""


def extensions(graph, primary_first):
    """Construct the next typed operations; enumeration order is part of the version."""
    ordered_roles = ["primary", "supplemental"] if primary_first else ["supplemental", "primary"]
    if not graph:
        return [allocation_node(role, "owed") for role in ordered_roles]
    last = graph[-1]
    roles = [node["role"] for node in graph if node["op"] == "allocate"]
    if last["op"] == "residual":
        return [allocation_node(role, last["out"]) for role in ordered_roles if role not in roles]
    choices = [credit_node(roles)]
    if len(roles) == 1:
        choices.append(residual_node(last["role"], last["inputs"][0]))
    return choices


def search_graph_avoiding(signature, skipped_graphs, primary_first):
    """BFS over partial DAGs. A rejected cached graph can be excluded from fresh checks."""
    result = {"graph": [], "trace": [], "expansions": 0, "tested": 0}
    if signature != split_signature():
        return result
    frontier = [[]]
    for depth in range(4):
        following = []
        for partial in frontier:
            result["expansions"] += 1
            for node in extensions(partial, primary_first):
                graph = partial + [node]
                if node["op"] != "credit":
                    following.append(graph)
                    continue
                if graph in skipped_graphs:
                    continue
                result["tested"] += 1
                error = proof_error(signature, graph)
                result["trace"].append({"graph": graph, "reason": error or "verified"})
                if not error:
                    result["graph"] = graph
                    return result
        frontier = following
    return result


def search_graph(signature):
    return search_graph_avoiding(signature, [], False)


def bind_graph(graph, d, s, g):
    """Execute the typed DAG on target amounts; local policy is judged by the caller."""
    if funding_signature(d, s, g) is None or wiring_error(graph):
        return None
    values = {"owed": d, "primary_limit": s, "supplemental_limit": g}
    for node in graph:
        amounts = [values[port] for port in node["inputs"]]
        if node["op"] == "allocate":
            amount = min(amounts)
        elif node["op"] == "residual":
            amount = amounts[0] - amounts[1]
        else:
            amount = sum(amounts)
        values[node["out"]] = amount
    primary = values.get("primary_draw", 0)
    supplemental = values.get("supplemental_draw", 0)
    if primary != s or supplemental > g or values["credit"] != d:
        return None
    return {"primary": primary, "supplemental": supplemental, "credit": values["credit"]}
