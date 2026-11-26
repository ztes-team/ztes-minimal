def tau(k, w):
    n, p = w["n"], w["p"]
    if n != 4 + 2 * k:
        return False
    if p > 0:
        return p <= n // 2 and prime(p) and prime(n - p)
    for q in range(2, n // 2 + 1):
        if prime(q) and prime(n - q):
            return False
    return True
