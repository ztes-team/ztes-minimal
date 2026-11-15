def omega(n, primes, prev):
    # [ω] Sω of factor: factor n, reusing the last admitted certificate (D1: the record decides which).
    if n == prev["n"]:
        return None                                  # n is already factored: nothing to propose
    g = gcd(n, prev["n"])

    # The part of n shared with the reused certificate: its prime factors are already certified.
    from_cert = []
    rest = g
    for q in sorted(set(prev["factors"])):          # bounded loops only: no while
        for _ in range(64):
            if rest % q != 0:
                break
            from_cert.append(q)
            rest = rest // q

    # The cofactor n / g, factored only by primes that already have certificates.
    r = n // g
    from_primes = []
    for q in primes:
        for _ in range(64):
            if r % q != 0:
                break
            from_primes.append(q)
            r = r // q
    if r != 1:
        return None                                  # a factor lacks a prime certificate: wait for primes

    return {"n": n, "factors": sorted(from_cert + from_primes),
            "reused": prev["n"] if g > 1 else 0, "gcd": g}
