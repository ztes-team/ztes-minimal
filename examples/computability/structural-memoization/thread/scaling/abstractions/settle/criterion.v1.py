def tau(K, fundings, diagnoses, policies, plans, prior, w):
    # [τ] Sτ of settle: the target's own policy covers the diagnosis and every draw; only the first K
    #     tiers pay, each after the tier before it is exhausted; the credit is the loss.
    return settlement_valid(w, fundings, diagnoses, policies, plans, prior, K)
