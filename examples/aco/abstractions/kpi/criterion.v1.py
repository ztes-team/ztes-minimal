def tau(OPT, tours, best, profile, profiles, kpis, w):
    # [τ] Sτ of kpi: one measurement per profile, and every indicator equal to its definition.
    return profiles > kpis and len(tours) > 0 and w == measure(tours, best, profile, profiles, OPT)
