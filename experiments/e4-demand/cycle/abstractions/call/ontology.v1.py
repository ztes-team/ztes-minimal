def omega(ROOT, DEPS, k, calls):
    if k == 0:
        return {"n": ROOT}
    for n in calls:
        for a in DEPS[n]:
            if a not in calls:
                return {"n": a}
    return None
