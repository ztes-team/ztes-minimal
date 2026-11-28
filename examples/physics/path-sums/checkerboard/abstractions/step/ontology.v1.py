def omega(COIN, D, T, X, slices):
    # [ω] Sω of step: the first slice the question (T, X) needs that is not recorded, computed from
    #     the recorded slice before it by one step of the walk (lib.py).
    # [C] The record is the memo table: `slices` maps (t, lo, hi) to the recorded slice, so a slice
    #     that another question has already recorded is not computed again.
    for t in range(T + 1):
        c = support(t, T, X)
        if (t, c[0], c[1]) in slices:
            continue                                   # recorded: reused
        if t == 0:
            return initial()
        p = support(t - 1, T, X)
        if (t - 1, p[0], p[1]) not in slices:
            return None                                # ⊥: the slice before is not recorded (wait)
        return next_slice(COIN, D, T, X, slices[(t - 1, p[0], p[1])])[0]
    return None                                        # ⊥: every slice of this question is recorded
