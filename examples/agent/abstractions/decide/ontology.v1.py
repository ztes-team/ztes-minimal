def omega(proposals, decisions, ethics_v, energy_v, ecology_v):
    for t in sorted(proposals):
        if t not in decisions:
            if t not in ethics_v or t not in energy_v or t not in ecology_v:
                return None
            return {"t": t, "executed": ethics_v[t] and energy_v[t]["v"] and ecology_v[t]["v"]}
    return None
