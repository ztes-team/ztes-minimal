def omega(N, D, BETA, k, trail):
    # [ω] Ant k starts at city k mod N and builds its walk from the trail of the last K ants.
    # The record resolves every choice (D1): the same prefix gives the same walk.
    walk = quota_walk(N, D, BETA, k, trail)
    return {"k": k, "walk": walk, "length": tour_length(D, walk)}
