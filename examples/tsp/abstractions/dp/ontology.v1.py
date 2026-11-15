def omega(N, D, ORDER, done, cost):
    # [ω] Sω of dp: the next subproblem of Held–Karp,
    #     cost(S, j) = min over i in S∖{j} of cost(S∖{j}, i) + d(i, j).
    # [C] The record is the memo table: `done` counts the recorded subproblems and `cost` maps
    #     each recorded (S, j) to its cost. They are recorded in ORDER, so the next one is ORDER[done].
    if done >= len(ORDER):
        return None                                    # ⊥: every subproblem of this instance is recorded
    m, j = ORDER[done]                                 # D1: determined by the record, not chosen
    prev = m ^ (1 << j)
    if prev == 0:
        return {"mask": m, "j": j, "cost": D[0][j], "pred": 0}
    best = None
    for i in bits(prev, N):                            # the smallest predecessor among the minima
        if (prev, i) not in cost:
            return None                                # ⊥: a predecessor is not recorded (wait)
        c = cost[(prev, i)] + D[i][j]
        if best is None or c < best[0]:
            best = (c, i)
    return {"mask": m, "j": j, "cost": best[0], "pred": best[1]}
