def omega(ROUTE, fundings, evidence, prior):
    # [ω] Sω of a diagnosis: the first case of this route, in the order of the fundings, whose evidence is complete.
    return next_diagnosis(fundings, evidence, ROUTE, prior)
