def tau(K, RULES, PLANNER, fundings, diagnoses, snapshots, catalogue, prior, w):
    # [τ] Sτ of plan: Definition 12 — reuse is admitted only for the same reduced signature of funding
    #     and the same versions, a pattern of other versions only by a new proof under these; the
    #     checker proves the graph for the whole region of the signature.
    return plan_valid(w, fundings, diagnoses, snapshots, catalogue, prior, K, RULES, PLANNER)
