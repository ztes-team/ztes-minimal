def tau(M, TRANS, K, configs, verdicts, w):
    # [τ] Sτ of run: one transition, checked against the recorded configuration before it (D2).
    if w["m"] != M or M in verdicts:
        return False
    cs = history(M, K, configs)
    if len(cs) == 0:
        return w == initial(M)
    last = cs[-1]
    if last["state"] == "Z" or last["k"] >= K or certificate(cs, len(cs) - 1) is not None:
        return False
    return w == step(TRANS, last)
