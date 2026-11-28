def tau(steps, last, w):
    # [τ] Sτ of rule: one step, checked against the recorded step before it (D2).
    if steps == 0:
        return w == start()
    return last["b"] != -1 and w == rule(last)
