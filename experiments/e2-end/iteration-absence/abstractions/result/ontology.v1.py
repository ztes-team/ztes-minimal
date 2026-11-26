def omega(k, items, acc):
    if k > 0 or len(items) == 0 or len(acc) != len(items):
        return None
    return {"n": len(acc), "s": acc[len(acc) - 1]}
