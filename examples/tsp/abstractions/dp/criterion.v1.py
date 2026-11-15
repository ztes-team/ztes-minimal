def tau(N, D, cost, w):
    # [τ] Sτ of dp: check one subproblem against its recorded predecessors only, without search (D2).
    #     The criterion does not use ORDER: any correct subproblem not yet recorded is admissible.
    m, j = w["mask"], w["j"]
    if m == 0 or m & ((1 << N) - 2) != m or j not in bits(m, N):
        return False                                   # not a subproblem of this instance
    if (m, j) in cost:
        return False                                   # already recorded: never computed twice
    prev = m ^ (1 << j)
    if prev == 0:
        return w["cost"] == D[0][j] and w["pred"] == 0
    costs = {}
    for i in bits(prev, N):
        if (prev, i) not in cost:
            return False                               # a predecessor is not recorded
        costs[i] = cost[(prev, i)] + D[i][j]
    return w["pred"] in costs and w["cost"] == costs[w["pred"]] == min(costs.values())
