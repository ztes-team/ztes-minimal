def omega(N, Q, D, entry, tours):
    # [ω] Sω of tour: the optimal tour through the cities Q, read from the recorded subproblems.
    # While fewer than NEEDED subproblems are recorded this body is not evaluated ("requires").
    if any(t["cities"] == sorted(Q) for t in tours):
        return None                                    # ⊥: this question is already answered
    mask = mask_of(Q)
    ends = []
    for j in bits(mask, N):
        if (mask, j) not in entry:
            return None                                # ⊥: the subproblems for Q are not complete (wait)
        ends.append((entry[(mask, j)]["cost"] + D[j][0], j))
    length, j = min(ends)
    return {"cities": sorted(Q), "tour": follow(entry, mask, j), "length": length}
