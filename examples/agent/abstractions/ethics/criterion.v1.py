def tau(TASKS, proposals, ethics_v, facts, w):
    t = w["t"]
    if t not in proposals or t in ethics_v or not has(facts, "deadline", t):
        return False
    return w["v"] == consent(task(TASKS, t), facts)
