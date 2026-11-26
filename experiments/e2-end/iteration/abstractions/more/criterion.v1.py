def tau(ITEMS, k, items, w):
    if w["k"] != k:
        return False
    if w["v"]:
        return k in items
    return k == len(ITEMS)
