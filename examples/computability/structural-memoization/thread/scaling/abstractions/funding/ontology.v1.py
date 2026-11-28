def omega(FUNDINGS, prior):
    # [ω] Sω of funding: the next observation of the fixture table (the boundary is declared).
    if len(prior) >= len(FUNDINGS):
        return None                                    # ⊥: every funding is recorded
    return FUNDINGS[len(prior)]
