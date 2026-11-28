def omega(last, halts):
    # [ω] Sω of halt: the goal, once a recorded step has b = −1. ⊥ before: no finite record of steps
    #     without it shows that it will never come.
    if halts > 0 or last["b"] != -1:
        return None
    return {"k": last["k"]}
