def omega(TASKS, facts, comps):
    for f in facts:
        if f["kind"] == "measure" and f["executed"] and f["t"] not in comps:
            excess = f["water"] - task(TASKS, f["t"])["water"]
            if excess > 0:
                return {"t": f["t"], "m3": excess}
    return None
