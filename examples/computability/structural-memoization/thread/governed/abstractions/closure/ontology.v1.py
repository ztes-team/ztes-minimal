def omega(mandates, fees, refunds, prior):
    # [ω] Sω of closure: the compensation closes when its coverage is complete.
    for m in mandates:
        if find_case(prior, m["case"]) is None and covered(m, fees, refunds):
            return closure_for(m, refunds)
    return None
