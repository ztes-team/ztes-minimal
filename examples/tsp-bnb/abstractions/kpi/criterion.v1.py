def tau(proofs, profile, profiles, kpis, w):
    # [τ] Sτ of kpi: one measurement per profile, and every indicator equal to its definition.
    return profiles > kpis and w == measure(proofs, profile, profiles)
