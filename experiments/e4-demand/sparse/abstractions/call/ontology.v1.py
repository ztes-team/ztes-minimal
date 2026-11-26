def omega(ROOT, k, calls):
    if k == 0:
        return {"n": ROOT}
    for n in calls:
        for a in ([n // 2, n // 3] if n > 0 else []):
            if a not in calls:
                return {"n": a}
    return None
