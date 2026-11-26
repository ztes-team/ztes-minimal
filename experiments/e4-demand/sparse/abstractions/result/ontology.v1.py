def omega(ROOT, k, vals):
    if k > 0 or ROOT not in vals:
        return None
    return {"v": vals[ROOT]}
