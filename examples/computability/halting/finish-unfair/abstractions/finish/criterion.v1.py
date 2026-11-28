def tau(decisions, ticks, finishes, w):
    # [τ] Sτ of finish: admissible after an even number of ticks, at a decision for it (§6.2).
    f = next_finish(decisions, ticks, finishes)
    return f is not None and w == f
