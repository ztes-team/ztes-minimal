# Helper functions shared by the specifications of the aco system.
# A specification receives a copy of the helpers it uses, so its recorded form stays self-contained.

def dist(XY, a, b):
    """Manhattan distance between cities a and b."""
    return abs(XY[a][0] - XY[b][0]) + abs(XY[a][1] - XY[b][1])


def matrix(XY, N):
    """The distance matrix of the cities 0 … N-1."""
    return [[dist(XY, a, b) for b in range(N)] for a in range(N)]


def tour_length(D, walk):
    """The length of the closed tour that visits the cities in the order of the walk."""
    return sum(D[walk[i - 1]][walk[i]] for i in range(len(walk)))


def valid(walk, N):
    """Every city exactly once."""
    return sorted(walk) == [c for c in range(N)]


def cycle(walk):
    """The tour as a cycle from city 0, whatever the starting city and the direction of the walk."""
    i = walk.index(0)
    r = walk[i:] + walk[:i]
    if r[1] > r[-1]:
        r = [r[0]] + r[:0:-1]
    return r


def weights(D, BETA, trail, i, free):
    """[C] The weight of each free city j seen from i: trail(i, j) × (1 / distance)^BETA, exactly.

    The trail is read from the recorded tours of the window; no pheromone matrix is kept. An edge
    no ant has used has trail 1; each recorded tour that uses the edge, in either direction, adds
    shortest/length, where shortest is the shortest tour of the window.
    """
    shortest = min(x["length"] for x in trail) if trail else 1
    near = []
    for x in trail:
        p = x["walk"].index(i)
        near.append([x["walk"][p - 1], x["walk"][(p + 1) % len(x["walk"])]])
    out = []
    for j in free:
        t = Fraction(1)
        for a in range(len(trail)):
            if j in near[a]:
                t = t + Fraction(shortest, trail[a]["length"])
        out.append(t / D[i][j] ** BETA)
    return out


def quota_walk(N, D, BETA, k, trail):
    """[ω] The walk of ant k under the quota rule: no draw, the record keeps the proportions.

    Standing at i, the ant gives each free city j the share weight(j) / total, as the classical
    rule does. Instead of drawing, it looks at the ants of the window that stood at i with j
    still free (had) and at how many of them went to j (took), and goes to the city that is
    furthest behind its share: the largest share × (had + 1) − took. Ties go to the nearer
    city, then to the smaller number.
    """
    walk = [k % N]
    for step in range(N - 1):
        i = walk[-1]
        free = [j for j in range(N) if j not in walk]
        w = weights(D, BETA, trail, i, free)
        total = sum(w)
        best = None
        for a in range(len(free)):
            j = free[a]
            had = 0
            took = 0
            for x in trail:
                p = x["walk"].index(i)
                if j not in x["walk"][:p]:
                    had = had + 1
                    if p + 1 < N and x["walk"][p + 1] == j:
                        took = took + 1
            key = (w[a] / total * (had + 1) - took, -D[i][j], -j)
            if best is None or key > best[0]:
                best = (key, j)
        walk.append(best[1])
    return walk


def measure(tours, best, profile, profiles, OPT):
    """The indicators of the colony (KPI abstraction): what was tried, what was found, how far from the optimum."""
    rows = {r["abstraction"]: r for r in profile}
    cycles = sorted(cycle(x["walk"]) for x in tours)
    distinct = sum(1 for a in range(len(cycles)) if a == 0 or cycles[a] != cycles[a - 1])
    return {"profile": profiles, "tours": len(tours), "distinct": distinct,
            "best": best["length"], "found_by_ant": best["k"], "optimum": OPT,
            "gap_permille": (best["length"] - OPT) * 1000 // OPT,
            "tour_invocations": rows["tour"]["I"], "best_not_yet": rows["best"]["U"]}
