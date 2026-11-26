def omega(k, more, acc):
    if k > 0:
        return None
    for j, v in sorted(more.items()):
        if v == False:
            if j == 0:
                return {"n": 0, "s": 0}
            return {"n": j, "s": acc[j - 1]} if (j - 1) in acc else None
    return None
