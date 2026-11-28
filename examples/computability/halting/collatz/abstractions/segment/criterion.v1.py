def tau(L, last, w):
    # [τ] Sτ of segment: the piece is the one the record needs, every step is T, and it stops at the
    #     first value below n, or after L steps. Every m < n has reached 1, recorded earlier, so a
    #     piece that falls below n establishes that n reaches 1 (an induction over the record).
    n = number(last)
    if w["n"] != n:
        return False
    if n == 1:
        return w == {"n": 1, "path": [1], "below": True}
    start = last["path"][-1] if last["n"] == n else n
    p = w["path"]
    if len(p) < 2 or p[0] != start or any(p[q + 1] != collatz(p[q]) for q in range(len(p) - 1)):
        return False
    if any(p[q] < n for q in range(1, len(p) - 1)):
        return False                                   # it stops at the first value below n
    if len(p) > L + 1:
        return False                                   # at most L steps
    if w["below"]:
        return p[-1] < n
    return p[-1] >= n and len(p) == L + 1
