# Helper functions shared by the specifications of the finish-fair system.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# The tick/finish example of §6.2 with the scheduler made explicit: the lineage policy records which
# abstraction acts next, 0 for tick and 1 for finish. The decisions are acted on in order. A tick
# decision is acted on by a tick. A finish decision is acted on by finish when the number of ticks
# before it is even; at an odd number it is void, and the next decision is acted on.


def next_tick(decisions, ticks):
    """The tick the record needs next, {"k": k}; None if none is due, or if a finish comes first."""
    needed = 0
    for d in decisions:
        if d[0] == 0:
            needed += 1
            if needed > ticks:
                return {"k": needed}
        elif needed % 2 == 0:
            return None                                # a finish is due here: no tick passes it
    return None


def next_finish(decisions, ticks, finishes):
    """The finish the record needs, {"ticks": n}: at the first decision for finish that comes after
    an even number of ticks, once those ticks are recorded; None otherwise."""
    if finishes > 0:
        return None
    needed = 0
    for d in decisions:
        if d[0] == 0:
            needed += 1
            if needed > ticks:
                return None                            # a tick before it is not recorded yet
        elif needed % 2 == 0:
            return {"ticks": needed}
    return None
