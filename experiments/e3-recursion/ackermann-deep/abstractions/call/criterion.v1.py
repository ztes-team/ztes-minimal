def tau(M0, N0, calls, vals, w):
    # a call is recorded once; it is the root, or it is demanded by a recorded call
    d = (w["m"], w["n"])
    if d in calls:
        return False
    if d == (M0, N0):
        return True
    for c in calls:
        m, n = c
        if m > 0 and n == 0 and d == (m - 1, 1):
            return True
        if m > 0 and n > 0 and d == (m, n - 1):
            return True
        if m > 0 and n > 0 and (m, n - 1) in vals and d == (m - 1, vals[(m, n - 1)]):
            return True
    return False
