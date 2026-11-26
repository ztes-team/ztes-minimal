def omega(DEPS, calls, vals):
    for n in calls:
        if n in vals:
            continue
        if all(a in vals for a in DEPS[n]):
            return {"n": n, "v": (1 + sum(vals[a] for a in DEPS[n]))}
    return None
