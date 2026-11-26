def omega(TASKS, BATTERY0, CAPACITY, DIESEL_MAX, proposals, energy_v, facts, decisions):
    for t in sorted(proposals):
        if t not in energy_v:
            return energy_verdict(t, TASKS, facts, decisions, BATTERY0, CAPACITY, DIESEL_MAX)
    return None
