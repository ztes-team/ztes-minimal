def tau(D, T, PARTS, slices, patterns, w):
    # [τ] Sτ of pattern: the probabilities of the recorded slice T, once per experiment.
    if (T, PARTS) not in slices or any(p["parts"] == PARTS for p in patterns):
        return False
    return w == pattern(D, PARTS, slices[(T, PARTS)])
