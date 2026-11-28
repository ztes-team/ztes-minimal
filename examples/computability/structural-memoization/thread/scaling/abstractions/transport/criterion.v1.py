def tau(ROUTE, fundings, evidence, prior, w):
    # [τ] Sτ of a diagnosis: one per case, equal to what the evidence of the case establishes.
    f = find_case(fundings, w["case"])
    return f is not None and find_case(prior, w["case"]) is None and w == diagnosis_for(f, evidence, ROUTE)
