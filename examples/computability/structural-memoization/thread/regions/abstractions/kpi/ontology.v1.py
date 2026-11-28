def omega(snapshots, plans, catalogue, profiles, kpis):
    # [ω] Sω of kpi: per target the origin of its plan and the work of the search; per pattern its rules
    #     and the cases that used it; the cases that wait without a plan.
    if profiles == 0 or kpis >= profiles:
        return None                                    # ⊥: nothing new to measure
    return measure(snapshots, plans, catalogue)
