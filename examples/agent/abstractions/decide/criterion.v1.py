def tau(proposals, decisions, ethics_v, energy_v, ecology_v, w):
    t = w["t"]
    if t not in proposals or t in decisions:
        return False
    if t not in ethics_v or t not in energy_v or t not in ecology_v:
        return False
    return w["executed"] == (ethics_v[t] and energy_v[t]["v"] and ecology_v[t]["v"])
