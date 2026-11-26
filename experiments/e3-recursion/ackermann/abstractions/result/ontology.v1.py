def omega(M0, N0, vals, results):
    if (M0, N0) in results or (M0, N0) not in vals:
        return None
    return {"m": M0, "n": N0, "v": vals[(M0, N0)]}
