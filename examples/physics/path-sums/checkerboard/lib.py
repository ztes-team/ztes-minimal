# Helper functions shared by the specifications of the checkerboard system.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# The walk: at time t the state is a slice, the amplitudes R (moving right) and L (moving left) at
# the sites lo, lo + 1, …, hi. The coin is [[a, ib], [ib, a]] with a = COIN[0]/D, b = COIN[1]/D, so an
# amplitude of slice t is (p + iq)/Dᵗ and is recorded as the pair of integers [p, q]. One step
# applies the coin at every site and then moves R one site to the right and L one to the left:
#     R'(x) = a·R(x−1) + ib·L(x−1)        L'(x) = ib·R(x+1) + a·L(x+1)
# Expanded over paths, this is Feynman's checkerboard: a factor a for each step that keeps the
# direction and ib for each turn.


def support(t, T, X):
    """The sites of slice t that the question (T, X) needs, as [lo, hi]: the light cone of the source
    at site 0, and for a question about one amplitude (X an integer) also the backward light cone of X
    at time T. Nothing outside the second cone can reach X by time T, at one site per step.
    """
    if X is None:
        return [-t, t]
    return [max(-t, X - (T - t)), min(t, X + (T - t))]


def initial():
    """Slice 0: one particle at site 0, moving right."""
    return {"t": 0, "lo": 0, "R": [[1, 0]], "L": [[0, 0]], "norm": Fraction(1), "pruned": Fraction(0)}


def transfer(COIN, s):
    """One step of the walk from slice s, on the whole light cone: returns lo and the lists R, L of the
    sites lo … lo + len(R) − 1 (one site more on each side than s), as numerators over Dᵗ⁺¹.
    """
    a = COIN[0]
    b = COIN[1]
    lo = s["lo"] - 1
    n = len(s["R"])
    R = []
    L = []
    for k in range(n + 2):                     # the new site x = lo + k
        if 0 <= k - 2 < n:                     # R'(x) comes from site x − 1
            r = s["R"][k - 2]
            l = s["L"][k - 2]
            R.append([a * r[0] - b * l[1], a * r[1] + b * l[0]])
        else:
            R.append([0, 0])
        if 0 <= k < n:                         # L'(x) comes from site x + 1
            r = s["R"][k]
            l = s["L"][k]
            L.append([a * l[0] - b * r[1], a * l[1] + b * r[0]])
        else:
            L.append([0, 0])
    return lo, R, L


def probability(D, t, R, L):
    """Σ |R(x)|² + |L(x)|² over the sites of slice t: an exact rational."""
    return Fraction(sum(p[0] * p[0] + p[1] * p[1] for p in R) + sum(p[0] * p[0] + p[1] * p[1] for p in L), D ** (2 * t))


def next_slice(COIN, D, T, X, s):
    """The slice after s for the question (T, X), and the probability of the whole step before the cut.

    One transfer on the light cone, then the cut to the support of the question; "pruned" is the
    probability of the sites that the cut leaves out (0 when nothing is cut).
    """
    lo, R, L = transfer(COIN, s)
    t = s["t"] + 1
    cut = support(t, T, X)
    full = probability(D, t, R, L)
    R = R[cut[0] - lo: cut[1] - lo + 1]
    L = L[cut[0] - lo: cut[1] - lo + 1]
    kept = probability(D, t, R, L)
    return {"t": t, "lo": cut[0], "R": R, "L": L, "norm": kept, "pruned": full - kept}, full


def kernel(D, T, s):
    """The answer read from slice T: the probability |R(x)|² + |L(x)|² at each of its sites, and the total."""
    P = [Fraction(s["R"][k][0] ** 2 + s["R"][k][1] ** 2 + s["L"][k][0] ** 2 + s["L"][k][1] ** 2, D ** (2 * T))
         for k in range(len(s["R"]))]
    return {"T": T, "lo": s["lo"], "hi": s["lo"] + len(s["R"]) - 1, "P": P, "total": sum(P)}


def binomial(n, k):
    """n choose k."""
    if k < 0 or k > n:
        return 0
    return prod(range(n - k + 1, n + 1)) // prod(range(1, k + 1))


def keys(T, X):
    """The slices a question needs, by key (t, lo, hi)."""
    out = []
    for t in range(T + 1):
        c = support(t, T, X)
        out.append((t, c[0], c[1]))
    return out


def measure(QUESTIONS, slices, kernels, profile, profiles):
    """The indicators of the checkerboard execution (KPI abstraction)."""
    seen = set()
    reused = 0
    for q in QUESTIONS:
        for k in keys(q[0], q[1]):
            if k in seen:
                reused += 1
            seen.add(k)
    sites = sum(len(s["R"]) for s in slices.values())
    pruned = sum(2 * s["t"] + 1 - len(s["R"]) for s in slices.values())
    paths = 0
    for k in kernels:
        for x in range(k["lo"], k["hi"] + 1):
            if (k["T"] + x) % 2 == 0:
                paths += binomial(k["T"], (k["T"] + x) // 2)
    rows = {r["abstraction"]: r for r in profile}
    return {"profile": profiles, "questions": len(kernels), "slices": len(slices), "sites": sites,
            "pruned_sites": pruned, "reused": reused, "paths": paths,
            "kernel_invocations": rows["kernel"]["I"], "kernel_not_yet": rows["kernel"]["U"]}
