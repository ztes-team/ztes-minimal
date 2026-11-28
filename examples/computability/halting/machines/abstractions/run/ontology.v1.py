def omega(M, TRANS, K, configs, verdicts):
    # [ω] Sω of run: the next configuration of machine M, by one transition from the last recorded one.
    #     ⊥ at a halting configuration, once a verdict is recorded, at the bound K, or once the recorded
    #     configurations contain a certificate that the machine never halts.
    if M in verdicts:
        return None
    cs = history(M, K, configs)
    if len(cs) == 0:
        return initial(M)
    last = cs[-1]
    if last["state"] == "Z" or last["k"] >= K or certificate(cs, len(cs) - 1) is not None:
        return None
    return step(TRANS, last)
