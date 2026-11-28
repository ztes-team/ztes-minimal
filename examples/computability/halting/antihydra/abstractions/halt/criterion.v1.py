def tau(last, halts, w):
    # [τ] Sτ of halt: once, at the recorded step with b = −1.
    return halts == 0 and last["b"] == -1 and w == {"k": last["k"]}
