def tau(TASKS, BATTERY0, CAPACITY, DIESEL_MAX, proposals, energy_v, facts, decisions, w):
    t = w["t"]
    if t not in proposals or t in energy_v:
        return False
    return w == energy_verdict(t, TASKS, facts, decisions, BATTERY0, CAPACITY, DIESEL_MAX)
