def omega(verdicts, configs, profile, profiles, kpis):
    # [ω] Sω of kpi: measure once for each recorded profile (KPI are computed only when asked for).
    if profiles == 0 or kpis >= profiles:
        return None                                    # ⊥: nothing new to measure
    return measure(verdicts, configs, profile, profiles)
