def omega(N, exps, best, proofs):
    # [ω] When no open node has a bound below the best tour, the best tour is optimal: record the proof.
    if best["n"] != N or any(p["n"] == N for p in proofs):
        return None
    frontier = open_nodes(exps, N)
    if any(x["bound"] < best["length"] for x in frontier):
        return None                                    # the search is not finished: wait
    return {"n": N, "length": best["length"], "tour": best["tour"],
            "expanded": len(exps), "open_left": len(frontier)}
