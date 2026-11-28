def omega(FEES, CHANGE, certificates, decisions, fees, prior):
    # [ω] Sω of mandate: the decision of the board on an admitted certificate activates the governed
    #     change (R1). It proposes the rules r2, in which a reserve tier may pay, as specifications
    #     carried by this event. It waits until the fees of the case are debited, so that the affected
    #     set is the same under every schedule.
    if len(prior) > 0:
        return None                                    # ⊥: decided
    for d in decisions:
        c = find_case(certificates, d["case"])
        if c is not None and len(fees_of(fees, d["case"])) == len(fees_of(FEES, d["case"])):
            return {"case": d["case"], "ref": "mandate/" + d["case"], "certificate": c["ref"],
                    "decision": d["ref"], "rules": "r2", "specifications": CHANGE}
    return None
