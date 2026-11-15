def omega(OPT, tours, best, profile, profiles, kpis):
    # [ω] Sω of kpi: measure once for each recorded profile (KPI are computed only when asked for).
    if profiles == 0 or kpis >= profiles or not tours:
        return None                                    # ⊥: nothing new to measure
    return measure(tours, best, profile, profiles, OPT)
