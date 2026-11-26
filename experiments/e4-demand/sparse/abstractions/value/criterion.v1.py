def tau(calls, vals, w):
    n = w["n"]
    if n in vals or n not in calls:
        return False
    if not all(a in vals for a in ([n // 2, n // 3] if n > 0 else [])):
        return False
    return w["v"] == (1 if n == 0 else vals[n // 2] + vals[n // 3])
