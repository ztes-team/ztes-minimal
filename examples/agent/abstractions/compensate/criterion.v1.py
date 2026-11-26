def tau(TASKS, facts, comps, w):
    t = w["t"]
    if t in comps:
        return False
    m = facts_of(facts, "measure", t)
    return len(m) == 1 and m[0]["executed"] and m[0]["water"] - task(TASKS, t)["water"] == w["m3"] > 0
