def tau(ROOT, DEPS, k, calls, w):
    if w["n"] in calls:
        return False
    if k == 0:
        return w["n"] == ROOT
    for n in calls:
        if w["n"] in DEPS[n]:
            return True
    return False
