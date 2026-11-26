def omega(k, items, acc):
    if k not in items:
        return None
    return {"k": k, "s": (acc[k - 1] if k > 0 else 0) + items[k]}
