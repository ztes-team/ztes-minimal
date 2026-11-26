def tau(ITEMS, k, w):
    return w["k"] == k and k < len(ITEMS) and w["a"] == ITEMS[k]
