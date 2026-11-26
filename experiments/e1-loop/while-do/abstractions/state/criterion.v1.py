def tau(X0, k, states, verdicts, w):
    # own lineage: the position k and the previous state; foreign: one positive atom, guard(k-1) = true
    if w["k"] != k:
        return False
    if k == 0:
        return w["x"] == X0
    if verdicts.get(k - 1) != True:
        return False
    x = states[k - 1]
    return w["x"] == (x // 2 if x % 2 == 0 else 3 * x + 1)
