def tau(N, D, exps, best, w):
    # [τ] Admitted if the node is open and not pruned, and its children, with their costs and bounds,
    # are exactly right. Which open node is expanded is not a condition of admission (D2).
    match = [x for x in open_nodes(exps, N) if x["path"] == w["node"]]
    if w["n"] != N or not match or match[0]["bound"] >= best["length"]:
        return False
    return w["children"] == children(match[0]["path"], match[0]["cost"], D, N)
