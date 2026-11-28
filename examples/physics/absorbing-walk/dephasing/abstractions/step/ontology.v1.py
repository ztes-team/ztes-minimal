def omega(A, TRAP, START, D, U, Q, T_DECIDE, last, decisions):
    # [ω] Sω of step: the next slice. The walk has no bound; a window of the plan ends a run. At slice
    #     T_DECIDE it waits until compensation has recorded its decision, so that the history is the
    #     same under every schedule.
    if last["t"] < 0:
        return initial(len(A), TRAP, START)
    if last["t"] == T_DECIDE and decisions == 0:
        return None                                    # ⊥: waits for the decision (Not Yet)
    return next_slice(U, D, TRAP, Q, last)[0]
