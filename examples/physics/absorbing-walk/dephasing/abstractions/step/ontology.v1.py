def omega(A, TRAP, START, D, U, Q, last):
    # [ω] Sω of step: the next slice. The walk has no bound; a window of the plan ends a run.
    if last["t"] < 0:
        return initial(len(A), TRAP, START)
    return next_slice(U, D, TRAP, Q, last)[0]
