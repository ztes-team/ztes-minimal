def tau(A, TRAP, START, D, U, Q, T_DECIDE, last, decisions, w):
    # [τ] Sτ of step: it recomputes one step from the recorded slice before it (D2) and checks that
    #     the step before absorption has exactly the probability of that slice, so a U that is not
    #     unitary is refused at its first step. The dephasing strength must be in [0, 1], and no
    #     slice follows T_DECIDE before compensation has decided.
    if U is None or Q[1] < 1 or Q[0] < 0 or Q[0] > Q[1]:
        return False
    if w["t"] != last["t"] + 1 or (last["t"] == T_DECIDE and decisions == 0):
        return False
    if w["t"] == 0:
        return w == initial(len(A), TRAP, START)
    expected, whole = next_slice(U, D, TRAP, Q, last)
    return whole * last["den"] == sum(last["diag"]) * expected["den"] and w == expected
