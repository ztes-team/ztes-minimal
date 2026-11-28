def omega(D, T, X, slices, kernels):
    # [ω] Sω of kernel: the answer to the question (T, X), the probabilities |R|² + |L|² at time T,
    #     read from the recorded slice T. While fewer than NEEDED slices are recorded this body is
    #     not evaluated ("requires").
    c = support(T, T, X)
    if any(k["T"] == T and k["lo"] == c[0] and k["hi"] == c[1] for k in kernels):
        return None                                    # ⊥: this question is answered
    if (T, c[0], c[1]) not in slices:
        return None                                    # ⊥: slice T is not recorded (wait)
    return kernel(D, T, slices[(T, c[0], c[1])])
