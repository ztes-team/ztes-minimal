def omega(L, last):
    # [ω] Sω of segment: the next piece of a trajectory. The number is read from the last recorded
    #     piece, so it is never searched for.
    return next_piece(L, last)
