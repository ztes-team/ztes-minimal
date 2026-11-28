def tau(QUESTIONS, slices, kernels, profile, profiles, kpis, w):
    # [τ] Sτ of kpi: one measurement per profile, and every indicator equal to its definition.
    return profiles > kpis and w == measure(QUESTIONS, slices, kernels, profile, profiles)
