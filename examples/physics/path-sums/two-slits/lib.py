# Helper functions shared by the specifications of the two-slits system.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# The walk of the checkerboard system (see its lib.py), with a screen at time T0 that lets only the
# sites SLITS through. A slice holds one or more parts on the same sites: one part when the paths
# through the two slits are added (no detector), one part per slit when a detector at the slits
# keeps them apart. A part is a pair of lists R, L; an amplitude of slice t is (p + iq)/Dᵗ, recorded
# as the pair of integers [p, q], and the coin is a = COIN[0]/D, b = COIN[1]/D.


def initial():
    """Slice 0: one particle at site 0, moving right."""
    return {"t": 0, "lo": 0, "parts": [{"R": [[1, 0]], "L": [[0, 0]]}], "norm": Fraction(1), "absorbed": Fraction(0)}


def transfer(COIN, part):
    """One step of the walk for one part on the sites lo … hi: the part on lo − 1 … hi + 1."""
    A = COIN[0]
    B = COIN[1]
    n = len(part["R"])
    R = []
    L = []
    for k in range(n + 2):                     # the new site lo − 1 + k
        if 0 <= k - 2 < n:                     # R'(x) comes from site x − 1
            r = part["R"][k - 2]
            l = part["L"][k - 2]
            R.append([A * r[0] - B * l[1], A * r[1] + B * l[0]])
        else:
            R.append([0, 0])
        if 0 <= k < n:                         # L'(x) comes from site x + 1
            r = part["R"][k]
            l = part["L"][k]
            L.append([A * l[0] - B * r[1], A * l[1] + B * r[0]])
        else:
            L.append([0, 0])
    return {"R": R, "L": L}


def probability(D, t, part):
    """Σ |R(x)|² + |L(x)|² over the sites of one part of slice t: an exact rational."""
    return Fraction(sum(p[0] * p[0] + p[1] * p[1] for p in part["R"]) + sum(p[0] * p[0] + p[1] * p[1] for p in part["L"]),
                    D ** (2 * t))


def only(part, lo, sites):
    """The part with every amplitude outside the given sites set to 0."""
    return {"R": [part["R"][k] if lo + k in sites else [0, 0] for k in range(len(part["R"]))],
            "L": [part["L"][k] if lo + k in sites else [0, 0] for k in range(len(part["L"]))]}


def next_slice(COIN, D, T0, SLITS, PARTS, s):
    """The slice after s, and the probability of the whole step before the screen.

    At t = T0 the screen keeps only the slits; what it stops is "absorbed". With PARTS = 1 the two
    slits stay in one part, so their amplitudes add; with PARTS = 2 each slit becomes a part of its
    own (a which-path detector with orthogonal states), and the parts never add again.
    """
    t = s["t"] + 1
    lo = s["lo"] - 1
    moved = [transfer(COIN, p) for p in s["parts"]]
    full = sum(probability(D, t, p) for p in moved)
    if t == T0 and PARTS == 1:
        parts = [only(moved[0], lo, SLITS)]
    elif t == T0:
        parts = [only(moved[0], lo, [x]) for x in SLITS]
    else:
        parts = moved
    norm = sum(probability(D, t, p) for p in parts)
    return {"t": t, "lo": lo, "parts": parts, "norm": norm, "absorbed": full - norm}, full


def pattern(D, PARTS, s):
    """The probability at every site of slice s: Σ over its parts of |R(x)|² + |L(x)|²."""
    n = len(s["parts"][0]["R"])
    P = [Fraction(sum(p["R"][k][0] ** 2 + p["R"][k][1] ** 2 + p["L"][k][0] ** 2 + p["L"][k][1] ** 2 for p in s["parts"]),
                  D ** (2 * s["t"])) for k in range(n)]
    return {"parts": PARTS, "lo": s["lo"], "P": P, "total": sum(P)}


def measure(T0, patterns, slices, profile, profiles):
    """The indicators of the two-slits execution (KPI abstraction)."""
    one = [p for p in patterns if p["parts"] == 1]
    two = [p for p in patterns if p["parts"] == 2]
    shared = len([k for k in slices if k[0] < T0])         # the slices before the screen: one part
    out = {"profile": profiles, "slices": len(slices), "reused": shared if len(two) > 0 else 0,
           "through_permille": floor(1000 * two[0]["total"]) if two else 0,
           "same_total": len(one) > 0 and len(two) > 0 and one[0]["total"] == two[0]["total"],
           "interference_permille": 0}
    if one and two:
        diff = sum(abs(one[0]["P"][k] - two[0]["P"][k]) for k in range(len(one[0]["P"])))
        out["interference_permille"] = floor(1000 * diff / two[0]["total"])
    rows = {r["abstraction"]: r for r in profile}
    out["pattern_invocations"] = rows["pattern"]["I"]
    out["pattern_not_yet"] = rows["pattern"]["U"]
    return out
