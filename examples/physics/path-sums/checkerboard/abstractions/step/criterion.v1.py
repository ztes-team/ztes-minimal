def tau(COIN, D, T, X, slices, w):
    # [τ] Sτ of step: one slice, checked against the recorded slice before it only (D2).
    #     The criterion knows nothing of paths. It recomputes one step and checks that probability is
    #     conserved: the whole step has the probability of the slice before it, exactly. A coin that
    #     is not unitary (COIN[0]² + COIN[1]² ≠ D²) is therefore refused at its first step.
    t = w["t"]
    if t < 0 or t > T:
        return False
    c = support(t, T, X)
    if w["lo"] != c[0] or len(w["R"]) != c[1] - c[0] + 1 or len(w["L"]) != c[1] - c[0] + 1:
        return False                                   # not the support this question needs
    if (t, c[0], c[1]) in slices:
        return False                                   # already recorded: never computed twice
    if t == 0:
        return w == initial()
    p = support(t - 1, T, X)
    if (t - 1, p[0], p[1]) not in slices:
        return False                                   # the slice before is not recorded
    s = slices[(t - 1, p[0], p[1])]
    expected, full = next_slice(COIN, D, T, X, s)
    return full == s["norm"] and w == expected
