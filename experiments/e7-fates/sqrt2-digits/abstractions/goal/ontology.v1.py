def omega(K, k, digits):
    return {"k": K - 1} if k == 0 and (K - 1) in digits else None
