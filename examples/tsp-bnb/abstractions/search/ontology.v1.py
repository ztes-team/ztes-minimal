def omega(N, D, exps, best):
    # [ω] Branch and bound: expand the open node with the smallest lower bound (D1: a fixed rule over C).
    # Nodes whose bound reaches the recorded best tour are pruned: never expanded.
    frontier = [(x["bound"], x["path"], x["cost"]) for x in open_nodes(exps, N) if x["bound"] < best["length"]]
    if not frontier:
        return None                                    # nothing left below the best tour: wait
    bound, path, cost = min(frontier)
    return {"n": N, "node": path, "children": children(path, cost, D, N)}
