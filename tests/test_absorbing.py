"""Tests of the absorbing-walk examples (examples/physics/absorbing-walk): a quantum walk on four
nodes with an absorbing trap, and the classes of Theorem 4.

The record shows each slice, the certificate and the goals attained in its window. The tests check
what it cannot show by itself:
* every slice equals an independent exact computation;
* in `dark` the dark probability is 1/2 at every slice, and a wrong certificate is refused;
* the step with absorption has the eigenvalues 0, 1 and (7 ± 2√17·i)/13, which give class 𝔒 to
  `bright` beyond its window;
* in `dephasing` a compensation event, admissible only after the certificate, changes the regime,
  and the goals the certificate excluded are attained after it, with S_{t+1} <= (165/169)·S_t;
* with q = 1 the walk is a classical Markov chain; a step that is not unitary, or a dephasing
  strength outside [0, 1], is refused.
"""
from fractions import Fraction

import pytest

from conftest import ROOT, quiet
from ztes import model as evaluation
from ztes.substrate import lookups
from ztes.substrate.replay import verify
from ztes.substrate.store import DiskStore, MemoryStore, read
from ztes.system.authoring import read_directory
from ztes.system.report import check_expect
from ztes.system.system import System

WALK = ROOT / "examples" / "physics" / "absorbing-walk"
NAMES = ["bright", "dark", "dephasing"]
EVENTS = {"bright": 52, "dark": 53, "dephasing": 76}

_RUNS = {}


def run(name):
    """The record of one system under the agenda (computed once per test session)."""
    if name not in _RUNS:
        system, store = System(WALK / name), MemoryStore()
        system.run(store, log=quiet)
        _RUNS[name] = (system, list(read(store)))
    return _RUNS[name]


def execs(C, a):
    return [(n, e) for n, e in enumerate(C) if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == a]


def values(C, a):
    return [e["payload"] for _, e in execs(C, a)]


def variant(name, constants=None, step_q=None, plan=3, only=("step", "certificate")):
    """The record of a system with changed constants or dephasing strength (first plan steps only)."""
    m = read_directory(WALK / name)
    if constants:
        m["constants"] = dict(m["constants"], **constants)
    if step_q:
        for a in only:
            for k in ("ontology", "criterion"):
                m["specifications"][f"{a}/{k}.v1"]["constants"] = {"Q": step_q}
    system, store = System.from_dict(m), MemoryStore()
    system.plan = system.plan[:plan]
    system.run(store, log=quiet)
    return system, read(store)


# ---- the walk, written independently of lib.py ---------------------------------------------------

I = 1j
A = [[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]]
U13 = [[9, -6 * I, -6 * I, -4], [-6 * I, 9, -4, -6 * I], [-6 * I, -4, 9, -6 * I], [-4, -6 * I, -6 * I, 9]]


def gauss(z):
    """A Gaussian integer given as a Python complex with integer parts, as a pair of Fractions."""
    return (Fraction(int(z.real)), Fraction(int(z.imag)))


def gmul(x, y):
    return (x[0] * y[0] - x[1] * y[1], x[0] * y[1] + x[1] * y[0])


def gadd(x, y):
    return (x[0] + y[0], x[1] + y[1])


ZERO = (Fraction(0), Fraction(0))
U = [[(gauss(z)[0] / 13, gauss(z)[1] / 13) for z in row] for row in [[complex(z) for z in r] for r in U13]]


def evolve(start, qs):
    """ρ after each step: U, dephasing with q, absorption at node 1. Returns [(ρ, absorbed)]."""
    rho = [[ZERO] * 4 for _ in range(4)]
    rho[start - 1][start - 1] = (Fraction(1), Fraction(0))
    absorbed = Fraction(0)
    out = [(rho, absorbed)]
    for q in qs:
        UR = [[sum_(gmul(U[i][k], rho[k][j]) for k in range(4)) for j in range(4)] for i in range(4)]
        rho = [[sum_(gmul(UR[i][k], (U[j][k][0], -U[j][k][1])) for k in range(4)) for j in range(4)] for i in range(4)]
        rho = [[rho[i][j] if i == j else (rho[i][j][0] * (1 - q), rho[i][j][1] * (1 - q)) for j in range(4)]
               for i in range(4)]
        absorbed += rho[0][0][0]
        rho = [[ZERO if 0 in (i, j) else rho[i][j] for j in range(4)] for i in range(4)]
        out.append((rho, absorbed))
    return out


def sum_(xs):
    s = ZERO
    for x in xs:
        s = gadd(s, x)
    return s


def recorded(s):
    """The density matrix and absorbed probability of a recorded slice, as Fractions."""
    den = s["den"]
    rho = [[ZERO] * 4 for _ in range(4)]
    ks, m = [1, 2, 3], 0
    for a, k in enumerate(ks):
        rho[k][k] = (Fraction(s["diag"][a], den), Fraction(0))
        for b in range(a + 1, 3):
            re, im = s["off"][m]
            rho[k][ks[b]] = (Fraction(re, den), Fraction(im, den))
            rho[ks[b]][k] = (Fraction(re, den), Fraction(-im, den))
            m += 1
    return rho, Fraction(s["absorbed"], den)


# ---- every system --------------------------------------------------------------------------------

@pytest.mark.parametrize("name", NAMES)
def test_absorbing_example_is_well_formed_and_meets_its_expected_end(name):
    system, C = run(name)
    assert system.check(log=quiet) == []
    assert system.expect and check_expect(system, C, log=quiet) == []
    assert len(C) == EVENTS[name]


@pytest.mark.parametrize("name", NAMES)
def test_absorbing_example_replays_in_process_and_over_http(name, tmp_path):
    from fastapi.testclient import TestClient
    from ztes.service import HttpService, make_app
    system, C = run(name)
    assert verify(C) == []
    store = DiskStore(tmp_path)
    system = System(WALK / name)
    system.run(store, {a: HttpService(client=TestClient(make_app(store, a))) for a in system.abstractions}, log=quiet)
    assert [e["payload"] for e in read(store)] == [e["payload"] for e in C]


@pytest.mark.parametrize("name,start,qs", [("bright", 4, [0] * 40), ("dark", 2, [0] * 40),
                                          ("dephasing", 2, [0] * 20 + [Fraction(1, 4)] * 40)])
def test_every_slice_equals_an_independent_exact_computation(name, start, qs):
    _, C = run(name)
    slices = values(C, "step")
    assert [s["t"] for s in slices] == list(range(len(qs) + 1))
    for s, (rho, absorbed) in zip(slices, evolve(start, qs)):
        assert recorded(s) == (rho, absorbed)
        assert sum(rho[k][k][0] for k in range(4)) + absorbed == 1                  # probability conserved


def test_the_step_is_the_crank_nicolson_form_and_unitary():
    """(I + iA/3)·U = I − iA/3 exactly, and U·U† = I: the U of DESIGN.md, independently of cayley()."""
    for i in range(4):
        for j in range(4):
            lhs = sum_(gmul((Fraction(int(i == k)), Fraction(A[i][k], 3)), U[k][j]) for k in range(4))
            assert lhs == (Fraction(int(i == j)), Fraction(-A[i][j], 3))
            uu = sum_(gmul(U[i][k], (U[j][k][0], -U[j][k][1])) for k in range(4))
            assert uu == (Fraction(int(i == j)), Fraction(0))


# ---- dark ----------------------------------------------------------------------------------------

def test_dark_keeps_half_of_the_walk_from_the_trap_at_every_slice():
    _, C = run("dark")
    for s in values(C, "step"):
        rho, absorbed = recorded(s)
        assert (rho[1][1][0] + rho[2][2][0] - 2 * rho[1][2][0]) / 2 == Fraction(1, 2)     # ⟨d|ρ|d⟩/2, d = e₂ − e₃
        assert absorbed < Fraction(1, 2)
    assert values(C, "certificate") == [{"pair": [2, 3], "dark": "1/2", "bound": "1/2", "k": 2}]


def test_a_wrong_certificate_is_refused_and_dephasing_admits_none():
    """D2: the criterion checks Ud = d for the given pair, the dark part and the bound. Under the
    regime with Q = 1/4 there is no invariant: the ontology proposes nothing and a certificate
    proposed by hand is refused."""
    _, C = run("dark")
    n, e = execs(C, "certificate")[0]
    P, good = C[:n], e["payload"]
    tau = lookups.load(P, e["coord"]["criterion"])
    assert evaluation.judge(P, tau, good)
    assert not evaluation.judge(P, tau, dict(good, pair=[2, 4]))                      # U(e₂ − e₄) ≠ e₂ − e₄
    assert not evaluation.judge(P, tau, dict(good, pair=[1, 2]))                      # node 1 is the trap
    for pair in ([], [2], [2, 3, 4]):                                                 # total on its domain
        assert evaluation.judge(P, tau, dict(good, pair=pair)) is False
    assert not evaluation.judge(P, tau, dict(good, bound="1/3"))
    assert not evaluation.judge(P, tau, dict(good, k=3))

    _, D = run("dephasing")
    after = execs(D, "compensation")[0][0]                                            # the governing event
    P = D[:after + 1]
    tau = lookups.load(P, lookups.active(P, "certificate", "criterion"))
    omega = lookups.load(P, lookups.active(P, "certificate", "ontology"))
    assert tau["constants"]["Q"] == [1, 4]
    assert evaluation.realize(P, omega) is None
    assert [n < after for n, _ in execs(D, "certificate")] == [True]                 # one, before the change


# ---- bright --------------------------------------------------------------------------------------

def test_bright_the_step_with_absorption_has_no_other_eigenvalue_of_modulus_1():
    """PU (P removes node 1) satisfies λ(λ − 1)(13λ² − 14λ + 9) = 0, whose roots are 0, 1 and
    (7 ± 2√17·i)/13 with |λ|² = 9/13; the eigenvalue 1 belongs to d = e₂ − e₃ only. A start without a
    dark part, as node 4, is therefore absorbed completely: every goal is attained (class 𝔒)."""
    PU = [[ZERO if i == 0 else U[i][j] for j in range(4)] for i in range(4)]

    def mul(X, Y):
        return [[sum_(gmul(X[i][k], Y[k][j]) for k in range(4)) for j in range(4)] for i in range(4)]

    def lin(*terms):
        return [[sum_((c * X[i][j][0], c * X[i][j][1]) for c, X in terms) for j in range(4)] for i in range(4)]

    Id = [[(Fraction(int(i == j)), Fraction(0)) for j in range(4)] for i in range(4)]
    poly = mul(mul(PU, lin((1, PU), (-1, Id))), lin((13, mul(PU, PU)), (-14, PU), (9, Id)))
    assert all(x == ZERO for row in poly for x in row)
    d = [ZERO, (Fraction(1), Fraction(0)), (Fraction(-1), Fraction(0)), ZERO]
    assert [sum_(gmul(PU[i][k], d[k]) for k in range(4)) for i in range(4)] == d
    assert abs(complex(7, 2 * 17 ** 0.5) / 13) ** 2 == pytest.approx(9 / 13)

    _, C = run("bright")
    goals = values(C, "kpi")[-1]["goals"]
    for k, t in enumerate(goals, start=1):
        absorbed = [recorded(s)[1] for s in values(C, "step")]
        assert absorbed[t] >= 1 - Fraction(1, 2 ** k) > absorbed[t - 1]
    assert len(goals) == 21


# ---- dephasing -----------------------------------------------------------------------------------

def test_dephasing_restores_reachability_after_the_governed_change():
    """Corollary 9: under Q = 0 the certificate excludes every goal from k = 2 on; the compensation
    event that carries Q = 1/4 is admitted after it, at slice 20, and goal 2 is attained at slice 30.
    The payloads of slices 0 … 20 are those of `dark`."""
    _, C = run("dephasing")
    _, Dk = run("dark")
    assert values(C, "step")[:21] == values(Dk, "step")[:21]
    (c, _), = execs(C, "certificate")
    (g, e), = execs(C, "compensation")
    assert c < g and e["payload"]["from"] == 20 and e["payload"]["q"] == [1, 4]
    assert [s["abstraction"] + "/" + s["role"] for s in e["payload"]["specifications"]] == [
        "step/criterion", "step/ontology", "certificate/criterion", "certificate/ontology"]
    assert [s["t"] for n, s in [(n, x["payload"]) for n, x in execs(C, "step")] if n > g][0] == 21
    goals = values(C, "kpi")[-1]["goals"]
    assert goals[:2] == [22, 30] and all(t > 20 for t in goals)
    absorbed = [recorded(s)[1] for s in values(C, "step")]
    assert absorbed[29] < Fraction(3, 4) <= absorbed[30]
    assert verify(C) == []


def test_dephasing_remaining_probability_falls_by_at_least_165_169_per_step():
    """After a step with dephasing at least the share q of what remains is diagonal, and from node 2,
    3 or 4 one step moves at least 16/169 of a diagonal state to the trap, so S_{t+1} <= (1 − 16q/169)·S_t:
    for q = 1/4, (165/169)·S_t from t = 21 on. Hence S_t → 0 and every G_k is attained."""
    _, C = run("dephasing")
    S = [sum(recorded(s)[0][k][k][0] for k in range(4)) for s in values(C, "step")]
    assert all(S[t + 1] <= Fraction(165, 169) * S[t] for t in range(21, 60))
    assert min(abs(z) ** 2 for z in [complex(x) for x in U13[0][1:]]) == 16


def test_the_compensation_is_admissible_only_after_a_certificate():
    """The criterion of compensation is the authority (R1). Without a certificate the walk waits at
    slice 20 and no change is admitted; a decision that carries another q, or not the four
    specifications of step and certificate, or from another slice, is refused."""
    system, C = variant("dephasing", step_q=[1, 1], only=("certificate",))
    assert values(C, "certificate") == [] and values(C, "compensation") == []
    assert [s["t"] for s in values(C, "step")] == list(range(21))
    _, D = run("dephasing")
    (g, e), = execs(D, "compensation")
    good = e["payload"]
    tau = lookups.load(D[:g], e["coord"]["criterion"])
    assert evaluation.judge(D[:g], tau, good)
    assert not evaluation.judge(C, tau, good)                                          # no certificate recorded
    assert not evaluation.judge(D[:g], tau, dict(good, q=[1, 2]))
    assert not evaluation.judge(D[:g], tau, dict(good, specifications=good["specifications"][:2]))
    assert not evaluation.judge(D[:g], tau, dict(good, **{"from": 19}))
    assert evaluation.judge(D[:g], tau, dict(good, q=[])) is False


# ---- the classical limit and refusals ------------------------------------------------------------

def test_with_q_1_the_walk_is_a_classical_markov_chain():
    """With q = 1 the diagonal follows the chain with transition probabilities |U_ij|², which are
    81, 36, 36 and 16 out of 169 in each row, and the walk from node 2 is absorbed completely."""
    _, C = variant("dark", step_q=[1, 1])
    slices = values(C, "step")
    p = [Fraction(0), Fraction(1), Fraction(0), Fraction(0)]
    T = [[Fraction(int(abs(z) ** 2 + 0.5), 169) for z in row] for row in [[complex(z) for z in r] for r in U13]]
    absorbed = Fraction(0)
    for s in slices[1:]:
        p = [sum(T[i][j] * p[j] for j in range(4)) for i in range(4)]
        absorbed += p[0]
        p[0] = Fraction(0)
        rho, a = recorded(s)
        assert [rho[k][k][0] for k in range(4)] == p and a == absorbed
        assert all(rho[i][j] == ZERO for i in range(4) for j in range(4) if i != j)
    assert values(C, "certificate") == [] and absorbed > Fraction(99, 100)


def test_a_wrong_digit_a_step_that_is_not_unitary_or_a_strength_outside_0_1_is_refused():
    _, C = run("bright")
    n, e = execs(C, "step")[5]
    P, good = C[:n], e["payload"]
    tau = lookups.load(P, e["coord"]["criterion"])
    assert evaluation.judge(P, tau, good)
    assert not evaluation.judge(P, tau, dict(good, absorbed=good["absorbed"] + 1))

    # a directed edge 1 → 4: the Crank–Nicolson form is integral over D = 1525, and not unitary
    system, D = variant("bright", constants={"A": [[0, 1, 1, 1], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]], "D": 1525})
    assert [s["t"] for s in values(D, "step")] == [0] and system.states(D)["step"] == "closed"
    system, D = variant("bright", step_q=[5, 4])
    assert values(D, "step") == [] and system.states(D)["step"] == "closed"
