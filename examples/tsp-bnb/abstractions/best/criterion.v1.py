def tau(N, D, best, w):
    # [τ] Any valid tour shorter than the recorded best is admitted: it is an upper bound,
    # whatever produced it (the search or a seed).
    t = w["tour"]
    if w["n"] != N or len(t) != N + 1 or t[0] != 0 or t[-1] != 0 or sorted(t[:-1]) != [c for c in range(N)]:
        return False
    return tour_length(D, t) == w["length"] < best["length"]
