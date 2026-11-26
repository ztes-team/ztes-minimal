def omega(X0, k, states, verdicts):
    if k == 0:
        return {"k": 0, "x": X0}
    if verdicts.get(k - 1) != True:
        return None
    x = states[k - 1]
    return {"k": k, "x": x // 2 if x % 2 == 0 else 3 * x + 1}
