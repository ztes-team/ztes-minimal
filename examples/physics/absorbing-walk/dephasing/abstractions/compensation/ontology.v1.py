def omega(T_DECIDE, CHANGE, last, certificates, decisions):
    # [ω] Sω of compensation: an admitted diagnosis, the certificate, activates the compensation. It
    #     proposes the change Δ, dephasing with strength 1/4, as specifications carried by its decision.
    if decisions > 0 or last["t"] != T_DECIDE or len(certificates) == 0:
        return None                                    # ⊥: nothing to decide yet, or decided
    return {"from": last["t"], "q": [1, 4], "specifications": CHANGE}
