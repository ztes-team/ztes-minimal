def omega(k, verdicts):
    if k > 0:
        return None
    for j, v in sorted(verdicts.items()):
        if v == False:
            return {"k": j}
    return None
