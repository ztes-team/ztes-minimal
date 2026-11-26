def omega(k, states):
    if k not in states:
        return None
    return {"k": k, "v": states[k] != 1}
