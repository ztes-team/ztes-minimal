def omega(tours, best):
    # [ω] The shortest recorded tour (the earliest, among equals), if it improves the recorded best.
    # It is read from the whole lineage, not from the latest event: Axiom 0 does not fix which
    # abstraction is invoked next, so "the latest tour" would depend on the schedule.
    shortest = tours[0]
    for x in tours:
        if x["length"] < shortest["length"]:
            shortest = x
    return shortest if shortest["length"] < best["length"] else None
