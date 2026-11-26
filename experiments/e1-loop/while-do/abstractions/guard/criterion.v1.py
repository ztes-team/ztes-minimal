def tau(k, states, w):
    return w["k"] == k and k in states and w["v"] == (states[k] != 1)
