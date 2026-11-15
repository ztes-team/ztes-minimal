# Helper functions shared by the specifications of the tsp system.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# A subproblem (S, j) of Held–Karp is a set S ⊆ {1, …, N-1}, written as a bitmask, and a city
# j ∈ S: the shortest path from the depot 0 through every city of S, ending at j.


def dist(XY, a, b):
    """Manhattan distance between cities a and b."""
    return abs(XY[a][0] - XY[b][0]) + abs(XY[a][1] - XY[b][1])


def matrix(XY, N):
    """The distance matrix of the cities 0 … N-1 (a derived value: computed once per version)."""
    return [[dist(XY, a, b) for b in range(N)] for a in range(N)]


def bits(mask, N):
    """The cities 1 … N-1 contained in a bitmask."""
    return [c for c in range(1, N) if (mask >> c) & 1]


def order(N):
    """All subproblems (S, j) in the order in which `dp` records them (a derived value).

    By the largest city of S, then by |S|, then S, then j. Every predecessor (S∖{j}, i) comes
    before (S, j): its largest city is not larger, and if it is the same, S∖{j} is smaller.
    The order for N-1 cities is a prefix of the order for N, so when a city is added the
    subproblems already recorded are exactly the beginning of the new order.
    """
    full = (1 << N) - 2
    keyed = sorted([(m.bit_length() - 1, len(bits(m, N)), m) for m in range(2, full + 1, 2)])
    return [(m, j) for top, size, m in keyed for j in bits(m, N)]


def mask_of(Q):
    """The bitmask of a set of cities (city 0, the depot, is not part of S)."""
    m = 0
    for c in Q:
        if c != 0:
            m = m | (1 << c)
    return m


def tour_length(D, t):
    """The length of a closed tour t = [0, …, 0]."""
    return sum(D[t[i]][t[i + 1]] for i in range(len(t) - 1))


def follow(entry, mask, j):
    """The tour that ends at j, obtained by following the recorded predecessors back to city 0."""
    path = []
    m = mask
    for _ in range(64):
        if m == 0:
            break
        path.append(j)
        pred = entry[(m, j)]["pred"]
        m = m ^ (1 << j)
        j = pred
    return [0] + path[::-1] + [0]


def needed(Q):
    """How many subproblems a from-scratch Held–Karp run for the cities Q needs: k·2^(k-1), k = |Q|-1."""
    k = len([c for c in Q if c != 0])
    return k * (1 << (k - 1)) if k else 0


def measure(done, tours, profile, profiles):
    """The indicators of the tsp execution (KPI abstraction): reuse of recorded subproblems, wake-ups of tour."""
    rows = {r["abstraction"]: r for r in profile}
    need = sum(needed(t["cities"]) for t in tours)
    return {"profile": profiles, "questions": len(tours), "subproblems": done, "needed": need,
            "saved": need - done, "tour_invocations": rows["tour"]["I"], "tour_not_yet": rows["tour"]["U"]}
