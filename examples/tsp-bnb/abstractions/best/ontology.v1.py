def omega(N, exps, best):
    # [ω] The best complete tour found by the search so far, if it improves the recorded best.
    better = [x for x in leaves(exps, N) if x[0] < best["length"]]
    if not better:
        return None
    length, path = min(better)
    return {"n": N, "tour": path + [0], "length": length, "source": "search"}
