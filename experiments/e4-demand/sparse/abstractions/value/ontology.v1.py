def omega(calls, vals):
    for n in calls:
        if n in vals:
            continue
        if all(a in vals for a in ([n // 2, n // 3] if n > 0 else [])):
            return {"n": n, "v": (1 if n == 0 else vals[n // 2] + vals[n // 3])}
    return None
