def omega(fundings, diagnoses, policies, plans, prior):
    # [ω] Sω of settle: the draws of the plan, for the first planned case without a settlement.
    return next_settlement(fundings, diagnoses, policies, plans, prior)
