def omega(ITEMS, k):
    if k >= len(ITEMS):
        return None
    return {"k": k, "a": ITEMS[k]}
