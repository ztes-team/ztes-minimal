def tau(A, TRAP, slices, certificates, profile, profiles, kpis, w):
    # [τ] Sτ of kpi: one measurement per profile, and every indicator equal to its definition.
    return profiles > kpis and len(slices) > 0 and w == measure(A, TRAP, slices, certificates, profile, profiles)
