def omega(M0, N0, calls, vals):
    if (M0, N0) not in calls:
        return {"m": M0, "n": N0}
    for c in calls:
        m, n = c
        need = []
        if m > 0 and n == 0:
            need = [(m - 1, 1)]
        if m > 0 and n > 0:
            need = [(m, n - 1)]
            if (m, n - 1) in vals:
                need.append((m - 1, vals[(m, n - 1)]))
        for d in need:
            if d not in calls:
                return {"m": d[0], "n": d[1]}
    return None
