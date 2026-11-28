def omega(SEED, decisions, ticks, finishes):
    # [ω] Sω of policy: the next decision of a fair scheduler, computed from the recorded seed. It waits
    #     until every recorded decision has been acted on, so the decisions, and with them the whole
    #     record, are the same under every schedule.
    if finishes > 0 or next_tick(decisions, ticks) is not None or next_finish(decisions, ticks, finishes) is not None:
        return None                                    # ⊥: finished, or the last decision is not acted on
    return [draw(SEED, len(decisions))]
