def tau(calls, vals, w):
    # positive atoms: the call is recorded, and so are the values it needs; own lineage: once per call
    m, n, v = w["m"], w["n"], w["v"]
    if (m, n) in vals or (m, n) not in calls:
        return False
    if m == 0:
        return v == n + 1
    if n == 0:
        return vals.get((m - 1, 1)) == v
    if (m, n - 1) not in vals:
        return False
    return vals.get((m - 1, vals[(m, n - 1)])) == v
