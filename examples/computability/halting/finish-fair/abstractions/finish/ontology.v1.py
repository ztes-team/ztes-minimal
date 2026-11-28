def omega(decisions, ticks, finishes):
    # [ω] Sω of finish: finish, once a decision for it comes after an even number of recorded ticks.
    return next_finish(decisions, ticks, finishes)
