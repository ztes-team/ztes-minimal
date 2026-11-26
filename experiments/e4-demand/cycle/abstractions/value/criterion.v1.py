def tau(DEPS, calls, vals, w):
    n = w["n"]
    if n in vals or n not in calls:
        return False
    if not all(a in vals for a in DEPS[n]):
        return False
    return w["v"] == (1 + sum(vals[a] for a in DEPS[n]))
