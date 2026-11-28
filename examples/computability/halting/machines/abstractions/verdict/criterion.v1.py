def tau(M, K, configs, verdicts, w):
    # [τ] Sτ of verdict: the given halting configuration or certificate (i, j) is checked against the
    #     recorded configurations, without search (D2; Proposition 14 for a certificate).
    if w["m"] != M or M in verdicts:
        return False
    return checked(history(M, K, configs), w)
