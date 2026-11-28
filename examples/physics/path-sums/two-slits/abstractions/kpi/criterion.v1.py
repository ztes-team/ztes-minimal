def tau(T0, patterns, slices, profile, profiles, kpis, w):
    # [τ] Sτ of kpi: one measurement per profile, and every indicator equal to its definition.
    return profiles > kpis and w == measure(T0, patterns, slices, profile, profiles)
