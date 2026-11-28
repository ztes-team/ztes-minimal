def omega(A, TRAP, slices, certificates, profile, profiles, kpis):
    # [ω] Sω of kpi: measure once for each recorded profile (KPI are computed only when asked for).
    if profiles == 0 or kpis >= profiles or len(slices) == 0:
        return None                                    # ⊥: nothing new to measure
    return measure(A, TRAP, slices, certificates, profile, profiles)
