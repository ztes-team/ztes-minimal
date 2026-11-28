def tau(D, T, X, slices, kernels, w):
    # [τ] Sτ of kernel: the probabilities of the recorded slice T, once per question.
    c = support(T, T, X)
    if (T, c[0], c[1]) not in slices or any(k["T"] == T and k["lo"] == c[0] and k["hi"] == c[1] for k in kernels):
        return False
    return w == kernel(D, T, slices[(T, c[0], c[1])])
