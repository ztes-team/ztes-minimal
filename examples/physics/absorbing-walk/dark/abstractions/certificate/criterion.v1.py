def tau(A, TRAP, START, D, Q, U, certs, w):
    # [τ] Sτ of certificate: an inductive invariant (Proposition 14). If Ud = d and d is 0 at TRAP,
    #     every step with Q = 0 keeps ⟨d|ρ|d⟩, so at least p never reaches the trap and every goal
    #     'absorbed ≥ 1 − 2⁻ᵏ' with 2⁻ᵏ < p is unreachable at every prefix of every continuation.
    #     The check uses the step operator and the start of this regime, not the slices recorded.
    if certs > 0 or Q[0] != 0 or U is None:
        return False
    n = len(U)
    if len(w["pair"]) != 2:
        return False
    i = w["pair"][0] - 1
    j = w["pair"][1] - 1
    if not (0 <= i < j < n) or i == TRAP - 1 or j == TRAP - 1:
        return False
    d = [1 if k == i else (-1 if k == j else 0) for k in range(n)]
    for r in range(n):
        if sum(U[r][k][0] * d[k] for k in range(n)) != D * d[r] or sum(U[r][k][1] * d[k] for k in range(n)) != 0:
            return False                               # U d ≠ d
    p = darkness(n, TRAP, initial(n, TRAP, START), w["pair"])
    return p > 0 and w["dark"] == p and w["bound"] == 1 - p and w["k"] == least_k(p)
