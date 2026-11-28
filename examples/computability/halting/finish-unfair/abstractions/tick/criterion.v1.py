def tau(decisions, ticks, w):
    # [τ] Sτ of tick: exactly the tick the recorded decisions call for.
    t = next_tick(decisions, ticks)
    return t is not None and w == t
