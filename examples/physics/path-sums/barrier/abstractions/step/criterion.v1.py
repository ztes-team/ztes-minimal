def tau(OUT, IN, D, T, W, M, X0, PHASE, slices, w):
    # [τ] Sτ of step: one slice, checked against the recorded slice before it only (D2).
    #     It recomputes one step and checks that probability is conserved: the whole step has the
    #     probability of the slice before it, exactly; what the cut leaves out is "pruned".
    t = w["t"]
    if w["w"] != W or t < 0 or t > T or (W, t) in slices:
        return False
    if t == 0:
        return w == packet(W, M, X0, PHASE, D)
    if (W, t - 1) not in slices:
        return False
    s = slices[(W, t - 1)]
    expected, full = next_slice(OUT, IN, D, T, W, M, X0, s)
    return full == s["norm"] and w == expected
