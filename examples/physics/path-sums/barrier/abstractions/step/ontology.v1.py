def omega(OUT, IN, D, T, W, M, X0, PHASE, slices):
    # [ω] Sω of step: the first slice of the question with barrier width W that is not recorded,
    #     from the recorded slice before it by one step of the walk (lib.py).
    for t in range(T + 1):
        if (W, t) in slices:
            continue
        if t == 0:
            return packet(W, M, X0, PHASE, D)
        if (W, t - 1) not in slices:
            return None                                # ⊥: the slice before is not recorded (wait)
        return next_slice(OUT, IN, D, T, W, M, X0, slices[(W, t - 1)])[0]
    return None                                        # ⊥: every slice of this question is recorded
