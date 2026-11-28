def tau(mandates, fees, refunds, prior, w):
    # [τ] Sτ of closure: complete coverage; a closure with a party missing is refused.
    m = find_case(mandates, w["case"])
    return (m is not None and find_case(prior, w["case"]) is None and covered(m, fees, refunds)
            and w == closure_for(m, refunds) and w["amount"] == sum(x["amount"] for x in fees_of(fees, w["case"])))
