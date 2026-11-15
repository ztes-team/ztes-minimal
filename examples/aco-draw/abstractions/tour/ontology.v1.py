def omega(N, D, BETA, M, k, trail, rolls):
    # [ω] Ant k starts at city k mod N and uses draw number k. The draw is read from C, never
    # generated here: the realization stays a function of the record (S1.2).
    if k >= len(rolls):
        return None                                    # ⊥: its draw is not yet admitted
    walk = draw_walk(N, D, BETA, M, k, trail, rolls[k])
    return {"k": k, "walk": walk, "length": tour_length(D, walk)}
