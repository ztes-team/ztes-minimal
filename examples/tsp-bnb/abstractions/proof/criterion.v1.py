def tau(N, exps, best, proofs, w):
    # [τ] Checked against the record: every node not expanded has a bound at least the length of the
    # best tour. Each bound was checked when its expansion was admitted.
    if w["n"] != N or best["n"] != N or any(p["n"] == N for p in proofs):
        return False
    frontier = open_nodes(exps, N)
    return (all(x["bound"] >= best["length"] for x in frontier) and w["length"] == best["length"]
            and w["tour"] == best["tour"] and w["expanded"] == len(exps) and w["open_left"] == len(frontier))
