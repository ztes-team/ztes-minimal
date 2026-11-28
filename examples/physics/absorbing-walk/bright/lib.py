# Helper functions shared by the specifications of the absorbing-walk systems.
# A specification receives a copy of the helpers it uses (and only those), so its recorded form
# stays self-contained. They are pure functions of their arguments (language.py rules).
#
# A quantum walk on the nodes 1 … n of a graph with adjacency A; node TRAP is coupled to an
# absorbing trap. One step is the Crank–Nicolson form U = (I + iεA)⁻¹(I − iεA), ε = EPS[0]/EPS[1],
# then dephasing with strength q = Q[0]/Q[1], then absorption at TRAP. The state is a density
# matrix. A Gaussian number is a pair [re, im]; D·U has Gaussian integer entries, and a slice
# stores Gaussian integer numerators over the integer "den". Nodes are numbered from 1 in the
# payloads and the constants, from 0 inside these functions.


def cmul(x, y):
    """The product of two Gaussian numbers."""
    return [x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0]]


def cmatmul(X, Y):
    """The product of two square matrices of Gaussian numbers."""
    n = len(X)
    out = []
    for i in range(n):
        row = []
        for j in range(n):
            re = 0
            im = 0
            for k in range(n):
                p = cmul(X[i][k], Y[k][j])
                re += p[0]
                im += p[1]
            row.append([re, im])
        out.append(row)
    return out


def cadjoint(X):
    """The conjugate transpose of a square matrix of Gaussian numbers."""
    return [[[X[j][i][0], -X[j][i][1]] for j in range(len(X))] for i in range(len(X))]


def cayley(A, EPS, D):
    """D·U for U = (I + iεA)⁻¹(I − iεA), as Gaussian integers; None if D·U is not integral."""
    n = len(A)
    e = Fraction(EPS[0], EPS[1])
    M = [[[Fraction(1 if i == j else 0), e * A[i][j]] for j in range(n)]
         + [[Fraction(1 if i == j else 0), Fraction(0)] for j in range(n)] for i in range(n)]
    for c in range(n):                                  # Gauss–Jordan over the Gaussian rationals
        p = c
        for r in range(c, n):
            if M[r][c][0] != 0 or M[r][c][1] != 0:
                p = r
                break
        M[c], M[p] = M[p], M[c]
        a = M[c][c]
        m = a[0] * a[0] + a[1] * a[1]
        inv = [a[0] / m, -a[1] / m]
        M[c] = [cmul(inv, x) for x in M[c]]
        for r in range(n):
            if r != c:
                f = M[r][c]
                M[r] = [[M[r][k][0] - cmul(f, M[c][k])[0], M[r][k][1] - cmul(f, M[c][k])[1]] for k in range(2 * n)]
    U = []
    for i in range(n):
        row = []
        for j in range(n):
            re = Fraction(0)
            im = Fraction(0)
            for k in range(n):
                p = cmul(M[i][n + k], [Fraction(1 if k == j else 0), -e * A[k][j]])
                re += p[0]
                im += p[1]
            if (D * re).denominator != 1 or (D * im).denominator != 1:
                return None
            row.append([(D * re).numerator, (D * im).numerator])
        U.append(row)
    return U


def others(n, TRAP):
    """The nodes other than the trap node, from 0: the nodes a slice stores."""
    return [k for k in range(n) if k != TRAP - 1]


def full(n, TRAP, s):
    """The n × n matrix of numerators of slice s; the row and column of TRAP are 0."""
    ks = others(n, TRAP)
    N = [[[0, 0] for j in range(n)] for i in range(n)]
    m = 0
    for a in range(len(ks)):
        N[ks[a]][ks[a]] = [s["diag"][a], 0]
        for b in range(a + 1, len(ks)):
            N[ks[a]][ks[b]] = s["off"][m]
            N[ks[b]][ks[a]] = [s["off"][m][0], -s["off"][m][1]]
            m += 1
    return N


def packed(n, TRAP, N):
    """The diagonal and the upper off-diagonal entries of N over the nodes other than TRAP."""
    ks = others(n, TRAP)
    diag = [N[k][k][0] for k in ks]
    off = []
    for a in range(len(ks)):
        for b in range(a + 1, len(ks)):
            off.append(N[ks[a]][ks[b]])
    return diag, off


def initial(n, TRAP, START):
    """Slice 0: the walk at node START."""
    ks = others(n, TRAP)
    return {"t": 0, "diag": [1 if k == START - 1 else 0 for k in ks],
            "off": [[0, 0] for a in range(len(ks)) for b in range(a + 1, len(ks))], "absorbed": 0, "den": 1}


def next_slice(U, D, TRAP, Q, s):
    """The slice after s, and the trace of the step before absorption (a numerator over its den).

    U: ρ ↦ UρU†. Dephasing: every off-diagonal entry times 1 − q, q = Q[0]/Q[1]. Absorption: the
    probability at TRAP is added to "absorbed", and the row and column of TRAP are set to 0.
    """
    n = len(U)
    M = cmatmul(cmatmul(U, full(n, TRAP, s)), cadjoint(U))
    den = s["den"] * D * D
    if Q[0] > 0:
        M = [[[M[i][j][0] * Q[1], M[i][j][1] * Q[1]] if i == j
              else [M[i][j][0] * (Q[1] - Q[0]), M[i][j][1] * (Q[1] - Q[0])] for j in range(n)] for i in range(n)]
        den = den * Q[1]
    whole = sum(M[k][k][0] for k in range(n))
    absorbed = s["absorbed"] * (den // s["den"]) + M[TRAP - 1][TRAP - 1][0]
    diag, off = packed(n, TRAP, M)
    return {"t": s["t"] + 1, "diag": diag, "off": off, "absorbed": absorbed, "den": den}, whole


def darkness(n, TRAP, s, pair):
    """⟨d|ρ|d⟩/2 for d = e_i − e_j, the nodes of pair: the probability of slice s in that dark state."""
    N = full(n, TRAP, s)
    i = pair[0] - 1
    j = pair[1] - 1
    return Fraction(N[i][i][0] + N[j][j][0] - 2 * N[i][j][0], 2 * s["den"])


def twins(A, TRAP):
    """Pairs of nodes other than TRAP with the same neighbours, from 1: for them A(e_i − e_j) = 0."""
    n = len(A)
    return [[i + 1, j + 1] for i in range(n) for j in range(i + 1, n)
            if i != TRAP - 1 and j != TRAP - 1 and A[i] == A[j]]


def least_k(p):
    """The least k with 2⁻ᵏ < p: the first goal 'absorbed ≥ 1 − 2⁻ᵏ' that a dark part p excludes."""
    for k in range(1, 1000):
        if Fraction(1, 2 ** k) < p:
            return k
    return 0


def certify(A, TRAP, start):
    """The certificate of a regime: a twin pair whose dark state holds part of the start slice."""
    for pair in twins(A, TRAP):
        p = darkness(len(A), TRAP, start, pair)
        if p > 0:
            return {"pair": pair, "dark": p, "bound": 1 - p, "k": least_k(p)}
    return None


def attained(slices):
    """The first slice t of each goal 'absorbed ≥ 1 − 2⁻ᵏ', k = 1, 2, … , while one is attained."""
    out = []
    for k in range(1, 1000):
        t = -1
        for s in slices:
            if s["absorbed"] * 2 ** k >= (2 ** k - 1) * s["den"]:
                t = s["t"]
                break
        if t < 0:
            break
        out.append(t)
    return out


def measure(A, TRAP, slices, certificates, profile, profiles):
    """The indicators of an absorbing-walk execution (KPI abstraction)."""
    last = slices[-1]
    pairs = twins(A, TRAP)
    dark = darkness(len(A), TRAP, last, pairs[0]) if pairs else Fraction(0)
    return {"profile": profiles, "slices": len(slices), "certificates": len(certificates),
            "absorbed_ppm": floor(1000000 * Fraction(last["absorbed"], last["den"])),
            "dark_ppm": floor(1000000 * dark), "goals": attained(slices)}
