def omega(TASKS, proposals, ethics_v, facts):
    for t in sorted(proposals):
        if t not in ethics_v:
            if not has(facts, "deadline", t):
                return None
            return {"t": t, "v": consent(task(TASKS, t), facts)}
    return None
