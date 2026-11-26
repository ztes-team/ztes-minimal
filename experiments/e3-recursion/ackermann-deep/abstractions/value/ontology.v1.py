def omega(calls, vals):
    for c in calls:
        if c in vals:
            continue
        m, n = c
        if m == 0:
            return {"m": m, "n": n, "v": n + 1}
        if n == 0 and (m - 1, 1) in vals:
            return {"m": m, "n": n, "v": vals[(m - 1, 1)]}
        if n > 0 and (m, n - 1) in vals and (m - 1, vals[(m, n - 1)]) in vals:
            return {"m": m, "n": n, "v": vals[(m - 1, vals[(m, n - 1)])]}
    return None
