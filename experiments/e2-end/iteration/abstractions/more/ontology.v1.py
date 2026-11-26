def omega(ITEMS, k, items):
    if k < len(ITEMS):
        return {"k": k, "v": True} if k in items else None
    if k == len(ITEMS):
        return {"k": k, "v": False}
    return None
