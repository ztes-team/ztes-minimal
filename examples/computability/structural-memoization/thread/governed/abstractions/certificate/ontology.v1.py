def omega(K, RULES, fundings, snapshots, plans, prior):
    # [ω] Sω of certificate: a case has reached planning, and its loss exceeds what the first K tiers can pay.
    return next_certificate(fundings, snapshots, plans, prior, K, RULES)
