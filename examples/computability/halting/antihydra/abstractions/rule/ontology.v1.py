def omega(steps, last):
    # [ω] Sω of rule: the next step of the rules, from the last recorded one; ⊥ once b = −1 (halted).
    if steps == 0:
        return start()
    if last["b"] == -1:
        return None
    return rule(last)
