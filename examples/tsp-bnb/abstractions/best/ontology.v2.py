def omega(N, D, exps, best, prev):
    # [ω] As v1, and in addition: before anything is found for N cities, seed the upper bound from the
    # recorded optimal tour for N-1 cities, with the new city inserted where it costs least.
    if best["n"] != N and prev["n"] == N - 1:
        t, new = prev["tour"], N - 1
        delta, i = min((D[t[i]][new] + D[new][t[i + 1]] - D[t[i]][t[i + 1]], i) for i in range(len(t) - 1))
        return {"n": N, "tour": t[:i + 1] + [new] + t[i + 1:], "length": prev["length"] + delta, "source": "seed"}
    better = [x for x in leaves(exps, N) if x[0] < best["length"]]
    if not better:
        return None
    length, path = min(better)
    return {"n": N, "tour": path + [0], "length": length, "source": "search"}
