def tau(prior, w):
    # [τ] Sτ of funding: ordered tiers with positive limits and one payer each; one funding per case.
    return funding_valid(w) and find_case(prior, w["case"]) is None
