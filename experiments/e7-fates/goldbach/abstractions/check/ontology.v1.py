def omega(k):
    n = 4 + 2 * k
    for q in range(2, n // 2 + 1):
        if prime(q) and prime(n - q):
            return {"n": n, "p": q}
    return {"n": n, "p": 0}
