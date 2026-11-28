def omega(fundings, diagnoses, policies, plans, settlements, catalogue, prior):
    # [ω] Sω of snapshot: the cut of the catalogue that the next case may read, the publications of the
    #     precedents its policy accepts. It waits until every earlier case is done.
    return next_snapshot(fundings, diagnoses, policies, plans, settlements, catalogue, prior)
