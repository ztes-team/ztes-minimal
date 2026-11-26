def tau(k, items, acc, w):
    if w["k"] != k or k not in items:
        return False
    if k > 0 and (k - 1) not in acc:
        return False
    return w["s"] == (acc[k - 1] if k > 0 else 0) + items[k]
