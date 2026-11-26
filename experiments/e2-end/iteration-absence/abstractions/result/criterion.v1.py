def tau(k, items, acc, w):
    return k == 0 and len(items) > 0 and len(acc) == len(items) == w["n"] and acc[w["n"] - 1] == w["s"]
