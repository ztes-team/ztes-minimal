def tau(N, Q, D, entry, tours, w):
    # [τ] Sτ of tour: admitted if it is a tour through Q, its length is right, and it is optimal:
    #     its length equals the minimum over the recorded subproblems, each of which was checked
    #     when it was admitted (D2: a chain of local checks, replayed by R2).
    t = w["tour"]
    if w["cities"] != sorted(Q) or any(x["cities"] == sorted(Q) for x in tours):
        return False                                   # another question, or this one is answered
    if len(t) < 2 or t[0] != 0 or t[-1] != 0 or sorted(t[:-1]) != sorted(Q):
        return False                                   # not a closed tour through Q
    if tour_length(D, t) != w["length"]:
        return False
    mask = mask_of(Q)
    ends = []
    for j in bits(mask, N):
        if (mask, j) not in entry:
            return False
        ends.append(entry[(mask, j)]["cost"] + D[j][0])
    return w["length"] == min(ends)
