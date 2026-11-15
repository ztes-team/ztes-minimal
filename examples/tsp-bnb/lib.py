# Helper functions shared by the specifications of the tsp-bnb system.
# A specification receives a copy of the helpers it uses, so its recorded form stays self-contained.

def dist(XY, a, b):
    """Manhattan distance between cities a and b."""
    return abs(XY[a][0] - XY[b][0]) + abs(XY[a][1] - XY[b][1])


def matrix(XY, N):
    """The distance matrix of the cities 0 … N-1."""
    return [[dist(XY, a, b) for b in range(N)] for a in range(N)]


def children(path, cost, D, N):
    """The children of a search node, each with its cost and an admissible lower bound."""
    out = []
    for c in range(1, N):
        if c not in path:
            p = path + [c]
            k = cost + D[path[-1]][c]
            rest = [u for u in range(1, N) if u not in p]
            if rest:                                   # every remaining city is left exactly once
                b = k + min(D[c][u] for u in rest) + sum(min(D[u][v] for v in rest + [0] if v != u) for u in rest)
            else:
                b = k + D[c][0]                        # a complete tour: the bound is its length
            out.append({"path": p, "cost": k, "bound": b})
    return out


def open_nodes(exps, N):
    """The recorded nodes that are not yet expanded and are not complete tours (root included)."""
    expanded = [e["node"] for e in exps]
    nodes = [{"path": [0], "cost": 0, "bound": 0}]
    for e in exps:
        nodes.extend(e["children"])
    return [x for x in nodes if x["path"] not in expanded and len(x["path"]) < N]


def leaves(exps, N):
    """The complete tours among the recorded children: (length, path)."""
    return [(c["bound"], c["path"]) for e in exps for c in e["children"] if len(c["path"]) == N]


def tour_length(D, t):
    return sum(D[t[i]][t[i + 1]] for i in range(len(t) - 1))


def full_tree(N):
    """Internal nodes of the full search tree for N cities: (N-1)!/(N-1-k)! summed over k < N-1."""
    total = 0
    term = 1
    for k in range(N - 1):
        total = total + term
        term = term * (N - 1 - k)
    return total


def measure(proofs, profile, profiles):
    """The indicators of the branch-and-bound execution (KPI abstraction): pruning, and wake-ups."""
    rows = {r["abstraction"]: r for r in profile}
    instances = [{"n": p["n"], "expansions": p["expanded"], "full_tree": full_tree(p["n"]),
                  "open_left": p["open_left"]} for p in proofs]
    return {"profile": profiles, "instances": instances,
            "search_invocations": rows["search"]["I"], "search_not_yet": rows["search"]["U"],
            "best_invocations": rows["best"]["I"], "best_not_yet": rows["best"]["U"]}
