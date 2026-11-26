def tau(k, more, acc, w):
    if k != 0 or more.get(w["n"]) != False:
        return False
    return w["s"] == 0 if w["n"] == 0 else acc.get(w["n"] - 1) == w["s"]
