def tau(COIN, D, T, T0, SLITS, PARTS, slices, w):
    # [τ] Sτ of step: one slice, checked against the recorded slice before it only (D2).
    #     It recomputes one step and checks that probability is conserved: the whole step has the
    #     probability of the slice before it, exactly, and what the screen stops is recorded.
    t = w["t"]
    if t < 0 or t > T or w["lo"] != -t:
        return False
    if (t, len(w["parts"])) in slices or len(w["parts"]) != (PARTS if t >= T0 else 1):
        return False                                   # recorded already, or not this experiment
    if t == 0:
        return w == initial()
    before = (t - 1, PARTS if t - 1 >= T0 else 1)
    if before not in slices:
        return False
    s = slices[before]
    expected, full = next_slice(COIN, D, T0, SLITS, PARTS, s)
    return full == s["norm"] and w == expected
