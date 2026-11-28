# Helper functions shared by the specifications of the collatz system.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# T(n) = n/2 for even n, 3n + 1 for odd n. The goal for n is that its trajectory reaches 1. Numbers
# are taken in order, so when n is checked every m < n has reached 1 already; the trajectory of n
# is therefore followed only until it falls below n (its stopping time), and the record supplies
# the rest: an induction over the record.


def collatz(m):
    """One step of the map T."""
    return m // 2 if m % 2 == 0 else 3 * m + 1


def piece(L, n, start):
    """The trajectory of n from `start`, until the first value below n or for L steps."""
    path = [start]
    m = start
    for s in range(L):
        m = collatz(m)
        path.append(m)
        if m < n:
            return {"n": n, "path": path, "below": True}
    return {"n": n, "path": path, "below": False}


def number(last):
    """The number the record needs next. Numbers are checked in order, so it is read from the last
    piece: the next number if that piece fell below its number, the same number otherwise."""
    return last["n"] + 1 if last["below"] else last["n"]


def next_piece(L, last):
    """The piece the record needs next, continuing the last piece if that one did not fall below its
    number."""
    n = number(last)
    if n == 1:
        return {"n": 1, "path": [1], "below": True}               # 1 has reached 1
    if last["n"] == n:
        return piece(L, n, last["path"][-1])
    return piece(L, n, n)


def measure(pieces, profile, profiles):
    """The indicators of the collatz execution (KPI abstraction). The number of steps from each n to
    1 is read from the record: the steps of all its pieces plus those of the number it falls to."""
    to1 = {1: 0}
    steps = {}
    recorded = 0
    longest = [0, 1]
    for p in pieces:
        s = len(p["path"]) - 1
        recorded += s
        if s > longest[0]:
            longest = [s, p["n"]]
        steps[p["n"]] = steps.get(p["n"], 0) + s
        if p["below"] and p["n"] > 1:
            to1[p["n"]] = steps[p["n"]] + to1[p["path"][-1]]
    total = sum(to1.values())
    return {"profile": profiles, "numbers": len(to1), "recorded_steps": recorded, "steps_to_1": total,
            "saved_permille": floor(1000 * (total - recorded) / total) if total > 0 else 0,
            "longest": longest[0], "longest_n": longest[1]}
