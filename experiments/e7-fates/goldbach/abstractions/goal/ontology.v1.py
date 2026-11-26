def omega(k, checks):
    if k > 0:
        return None
    for n, p in sorted(checks.items()):
        if p == 0:
            return {"n": n}
    return None
