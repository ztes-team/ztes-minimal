def omega(TASKS, WATER_BUDGET, CO2_BUDGET, CO2_PER_KWH, proposals, ecology_v, energy_v, facts, decisions, comps):
    for t in sorted(proposals):
        if t not in ecology_v:
            return ecology_verdict(t, TASKS, facts, decisions, energy_v, comps, WATER_BUDGET, CO2_BUDGET, CO2_PER_KWH)
    return None
