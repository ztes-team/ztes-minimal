def omega(M, K, configs, verdicts):
    # [ω] Sω of verdict: halts, read from a recorded halting configuration; or never halts, with a
    #     certificate found by a search of the recorded configurations. ⊥ while there is neither:
    #     a missing verdict is not a verdict.
    if M in verdicts:
        return None
    cs = history(M, K, configs)
    if len(cs) == 0:
        return None
    last = cs[-1]
    if last["state"] == "Z":
        return {"m": M, "halts": True, "kind": "halt", "i": last["k"], "j": last["k"], "steps": last["k"],
                "ones": sum(last["tape"])}
    c = certificate(cs, len(cs) - 1)
    if c is None:
        return None
    return {"m": M, "halts": False, "kind": c[0], "i": c[1], "j": last["k"], "steps": last["k"],
            "ones": sum(last["tape"])}
