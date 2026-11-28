def omega(K, RULES, PLANNER, fundings, diagnoses, snapshots, catalogue, prior):
    # [ω] Sω of plan: under the rules in force (K tiers may pay), reduce the funding of the next case to
    #     its signature. In its declared cut, reuse a publication of that signature and these versions;
    #     else check again one of that signature derived under other versions; else search. A case
    #     above the bound of K tiers has no plan (⊥).
    return next_plan(fundings, diagnoses, snapshots, catalogue, prior, K, RULES, PLANNER)
