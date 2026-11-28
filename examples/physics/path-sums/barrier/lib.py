# Helper functions shared by the specifications of the barrier system.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# The walk of the checkerboard system (see its lib.py) with a coin that depends on the site: OUT
# everywhere, IN on the barrier, the sites 0 … W − 1. A coin is [a, b] as numerators over D, so an
# amplitude of slice t is (p + iq)/D^(M + t), recorded as the pair of integers [p, q]. IN has a
# smaller a, a larger mass: a wave whose frequency lies in the gap of IN has no propagating mode
# inside and decays there (a mass barrier). The particle starts as a packet: a binomial envelope,
# close to a Gaussian, times the phase zʲ, z = (PHASE[0] + i·PHASE[1])/√D, that moves it to the right.


def probability(D, e, R, L):
    """Σ |R(x)|² + |L(x)|² over the sites of a slice whose amplitudes are numerators over Dᵉ: an exact rational."""
    return Fraction(sum(p[0] * p[0] + p[1] * p[1] for p in R) + sum(p[0] * p[0] + p[1] * p[1] for p in L), D ** (2 * e))


def packet(W, M, X0, PHASE, D):
    """Slice 0 of the question with barrier width W (not normalized): R(x) = C(2M, j)·zʲ at
    x = X0 − M + j, j = 0 … 2M, and L = 0, as numerators over D^M = √D^(2M).
    """
    root = isqrt(D)
    R = []
    phase = [1, 0]                             # (PHASE[0] + i·PHASE[1])ʲ
    c = 1                                      # C(2M, j)
    for j in range(2 * M + 1):
        scale = c * root ** (2 * M - j)
        R.append([scale * phase[0], scale * phase[1]])
        phase = [phase[0] * PHASE[0] - phase[1] * PHASE[1], phase[0] * PHASE[1] + phase[1] * PHASE[0]]
        c = c * (2 * M - j) // (j + 1)
    L = [[0, 0] for j in range(2 * M + 1)]
    return {"w": W, "t": 0, "lo": X0 - M, "R": R, "L": L, "norm": probability(D, M, R, L), "pruned": Fraction(0)}


def support(t, T, W, M, X0):
    """The sites of slice t that the question needs, as [lo, hi]: the light cone of the packet, cut on
    the left where a site could not reach the far side of the barrier (x ≥ W) by time T at one site
    per step. Only the transmitted probability at T is asked for.
    """
    return [max(X0 - M - t, W - (T - t)), X0 + M + t]


def coin(OUT, IN, W, x):
    """[a, b] at site x, as numerators over D."""
    return IN if 0 <= x < W else OUT


def transfer(OUT, IN, W, s):
    """One step of the walk from slice s, on its whole light cone: lo and the lists R, L."""
    lo = s["lo"] - 1
    n = len(s["R"])
    R = []
    L = []
    for k in range(n + 2):                     # the new site x = lo + k
        if 0 <= k - 2 < n:                     # R'(x) comes from site x − 1, through its coin
            a, b = coin(OUT, IN, W, lo + k - 1)
            r = s["R"][k - 2]
            l = s["L"][k - 2]
            R.append([a * r[0] - b * l[1], a * r[1] + b * l[0]])
        else:
            R.append([0, 0])
        if 0 <= k < n:                         # L'(x) comes from site x + 1, through its coin
            a, b = coin(OUT, IN, W, lo + k + 1)
            r = s["R"][k]
            l = s["L"][k]
            L.append([a * l[0] - b * r[1], a * l[1] + b * r[0]])
        else:
            L.append([0, 0])
    return lo, R, L


def next_slice(OUT, IN, D, T, W, M, X0, s):
    """The slice after s, and the probability of the whole step before the cut ("pruned" is cut off)."""
    lo, R, L = transfer(OUT, IN, W, s)
    t = s["t"] + 1
    cut = support(t, T, W, M, X0)
    full = probability(D, M + t, R, L)
    R = R[cut[0] - lo: cut[1] - lo + 1]
    L = L[cut[0] - lo: cut[1] - lo + 1]
    kept = probability(D, M + t, R, L)
    return {"w": W, "t": t, "lo": cut[0], "R": R, "L": L, "norm": kept, "pruned": full - kept}, full


def measure(M, transmitted, slices, profile, profiles):
    """The indicators of the barrier execution (KPI abstraction)."""
    rows = {r["abstraction"]: r for r in profile}
    sites = sum(len(s["R"]) for s in slices.values())
    cone = sum(2 * M + 1 + 2 * s["t"] for s in slices.values())
    return {"profile": profiles, "widths": [x["w"] for x in transmitted],
            "transmitted_ppm": [floor(1000000 * x["transmitted"]) for x in transmitted],
            "slices": len(slices), "sites": sites, "pruned_sites": cone - sites,
            "transmission_invocations": rows["transmission"]["I"], "transmission_not_yet": rows["transmission"]["U"]}
