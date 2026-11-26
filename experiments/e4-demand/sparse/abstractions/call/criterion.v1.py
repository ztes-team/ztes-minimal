def tau(ROOT, k, calls, w):
    if w["n"] in calls:
        return False
    if k == 0:
        return w["n"] == ROOT
    for n in calls:
        if w["n"] in ([n // 2, n // 3] if n > 0 else []):
            return True
    return False
