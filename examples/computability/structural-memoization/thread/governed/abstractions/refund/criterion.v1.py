def tau(mandates, fees, prior, w):
    # [τ] Sτ of refund: the party was affected, is not yet refunded, and the refund cites its debits.
    m = find_case(mandates, w["case"])
    return (m is not None and w["actor"] in affected(fees, w["case"]) and not refunded(prior, w["case"], w["actor"])
            and w == refund_for(m, w["actor"], fees))
