def tau(TASKS, WATER_BUDGET, CO2_BUDGET, CO2_PER_KWH, proposals, ecology_v, energy_v, facts, decisions, comps, w):
    t = w["t"]
    if t not in proposals or t in ecology_v:
        return False
    return w == ecology_verdict(t, TASKS, facts, decisions, energy_v, comps, WATER_BUDGET, CO2_BUDGET, CO2_PER_KWH)
