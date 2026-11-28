"""Tests of the physics examples (examples/physics/path-sums): Feynman's sum over paths on a lattice.

Each system computes the sum slice by slice, as a memo table in the record. The tests check what
the record cannot show by itself: that the slices equal the sum over every path (by enumeration and
by a closed form), that pruning and reuse change no value, that the two-slit patterns differ by the
interference term only, that tunnelling decreases with the width of the barrier, and how a Monte
Carlo estimate of the same sum fares (the sign problem).
"""
import random
from fractions import Fraction
from itertools import product
from math import comb

import pytest

from conftest import ROOT, quiet
from ztes import model as evaluation
from ztes.substrate import lookups
from ztes.substrate.replay import verify
from ztes.substrate.store import DiskStore, MemoryStore, read
from ztes.system.report import LONG, check_expect, show
from ztes.system.system import System

PHYSICS = ROOT / "examples" / "physics" / "path-sums"
NAMES = ["checkerboard", "two-slits", "barrier"]
EVENTS = {"checkerboard": 50, "two-slits": 89, "barrier": 237}

_RUNS = {}


def run(name):
    """The record of one system under the agenda (computed once per test session)."""
    if name not in _RUNS:
        system, store = System(PHYSICS / name), MemoryStore()
        system.run(store, log=quiet)
        _RUNS[name] = (system, list(read(store)))
    return _RUNS[name]


def values(C, a):
    return [e["payload"] for e in C if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == a]


def exact(p, scale):
    """A recorded amplitude [p, q] of a slice whose amplitudes are numerators over `scale`."""
    return (Fraction(p[0], scale), Fraction(p[1], scale))


# ---- the walk, written independently of lib.py -------------------------------------------------

def cmul(z, w):
    return (z[0] * w[0] - z[1] * w[1], z[0] * w[1] + z[1] * w[0])


def cadd(z, w):
    return (z[0] + w[0], z[1] + w[1])


ZERO = (Fraction(0), Fraction(0))


def walk(a, b, R, L, steps, coin=None):
    """The walk on dicts site → amplitude, without any cut: R'(x) = a R(x−1) + ib L(x−1), L'(x) = ib R(x+1) + a L(x+1).
    coin(x) gives (a, b) at site x when it depends on the site."""
    for _ in range(steps):
        R2, L2 = {}, {}
        for x in set(R) | set(L):
            ax, bx = coin(x) if coin else (a, b)
            r, l = R.get(x, ZERO), L.get(x, ZERO)
            A, iB = (ax, Fraction(0)), (Fraction(0), bx)
            R2[x + 1] = cadd(R2.get(x + 1, ZERO), cadd(cmul(A, r), cmul(iB, l)))
            L2[x - 1] = cadd(L2.get(x - 1, ZERO), cadd(cmul(iB, r), cmul(A, l)))
        R, L = R2, L2
    return R, L


A, B = Fraction(4, 5), Fraction(3, 5)


def turn_counts(T):
    """Enumerate all 2ᵀ direction sequences of a particle that starts at 0 moving right:
    (end site, final direction, number of turns) → number of paths."""
    counts = {}
    for ds in product((1, -1), repeat=T):
        prev, turns = 1, 0
        for d in ds:
            turns += d != prev
            prev = d
        k = (sum(ds), prev, turns)
        counts[k] = counts.get(k, 0) + 1
    return counts


def weight(T, turns):
    """The amplitude of one path with this many turns: a^(T − turns) · (ib)^turns."""
    w = (A ** (T - turns), Fraction(0))
    for _ in range(turns):
        w = cmul(w, (Fraction(0), B))
    return w


def closed_form(T, x):
    """The amplitudes (R, L) at (x, T) from the number of paths with a given number of turns:
    ending right with 2k turns, C(r, k)·C(l−1, k−1); ending left with 2k+1 turns, C(r, k)·C(l−1, k);
    r = (T + x)/2 steps to the right, l = (T − x)/2 to the left."""
    r, l = (T + x) // 2, (T - x) // 2
    R, L = ZERO, ZERO
    if l == 0:
        R = weight(T, 0)
    for k in range(1, T + 1):
        n = comb(r, k) * comb(l - 1, k - 1) if l >= 1 else 0
        if n:
            w = weight(T, 2 * k)
            R = cadd(R, (n * w[0], n * w[1]))
    for k in range(0, T + 1):
        n = comb(r, k) * comb(l - 1, k) if l >= 1 else 0
        if n:
            w = weight(T, 2 * k + 1)
            L = cadd(L, (n * w[0], n * w[1]))
    return R, L


# ---- every system --------------------------------------------------------------------------------

@pytest.mark.parametrize("name", NAMES)
def test_physics_example_is_well_formed_and_meets_its_expected_end(name):
    system, C = run(name)
    assert system.check(log=quiet) == []
    assert system.expect and check_expect(system, C, log=quiet) == []
    assert len(C) == EVENTS[name]


@pytest.mark.parametrize("name", NAMES)
def test_physics_example_replays_in_process_and_over_http(name, tmp_path):
    from fastapi.testclient import TestClient
    from ztes.service import HttpService, make_app
    system, C = run(name)
    assert verify(C) == []
    store = DiskStore(tmp_path)
    system = System(PHYSICS / name)
    system.run(store, {a: HttpService(client=TestClient(make_app(store, a))) for a in system.abstractions}, log=quiet)
    assert [e["payload"] for e in read(store)] == [e["payload"] for e in C]


def test_long_values_are_shown_shortened():
    """The record of a physics example has values of thousands of characters; run shows their beginning."""
    _, C = run("two-slits")
    lines = []
    show(C, log=lines.append)
    assert max(len(x) for x in lines) < LONG + 50 and any("characters)" in x for x in lines)


# ---- checkerboard ----------------------------------------------------------------------------------

def test_checkerboard_equals_the_sum_over_all_paths():
    """T = 16: the recorded slice equals the sum over all 65,536 paths, exactly, and the closed form."""
    _, C = run("checkerboard")
    s = next(p for p in values(C, "step") if p["t"] == 16)
    counts = turn_counts(16)
    assert sum(counts.values()) == 2 ** 16
    for k, x in enumerate(range(s["lo"], s["lo"] + len(s["R"]))):
        R, L = ZERO, ZERO
        for (end, final, turns), n in counts.items():
            if end == x:
                w = weight(16, turns)
                if final == 1:
                    R = cadd(R, (n * w[0], n * w[1]))
                else:
                    L = cadd(L, (n * w[0], n * w[1]))
        assert (exact(s["R"][k], 5 ** 16), exact(s["L"][k], 5 ** 16)) == (R, L)
        if (16 + x) % 2 == 0:
            assert (R, L) == closed_form(16, x)


def test_checkerboard_one_amplitude_on_two_cones_needs_no_more():
    """Question 2 cuts the slices to the cone of x = 0 at T = 32: the amplitude equals the closed form
    (2³² paths cannot be enumerated) and a computation on the whole cone; the cut probability is recorded."""
    _, C = run("checkerboard")
    s = next(p for p in values(C, "step") if p["t"] == 32)
    assert s["lo"] == 0 and len(s["R"]) == 1
    got = (exact(s["R"][0], 5 ** 32), exact(s["L"][0], 5 ** 32))
    assert got == closed_form(32, 0)
    R, L = walk(A, B, {0: (Fraction(1), Fraction(0))}, {}, 32)
    assert got == (R.get(0, ZERO), L.get(0, ZERO))
    slices = values(C, "step")
    assert Fraction(s["norm"]) + sum(Fraction(p["pruned"]) for p in slices) == 1      # probability conserved
    assert all(Fraction(p["norm"]) == 1 for p in slices if p["t"] <= 16)


def test_checkerboard_reuses_and_never_computes_a_slice_twice():
    _, C = run("checkerboard")
    keys = [(p["t"], p["lo"], p["lo"] + len(p["R"]) - 1) for p in values(C, "step")]
    assert len(keys) == len(set(keys)) == 33                 # 17 for question 1, 16 new for question 2
    at = [n for n, e in enumerate(C) if e["coord"].get("abstraction") == "kernel" and e["coord"]["kind"] == "exec"]
    first_new = next(e["payload"]["t"] for e in C[at[0]:] if e["coord"].get("abstraction") == "step"
                     and e["coord"]["kind"] == "exec")
    assert first_new == 17                                   # slices 0–16 of question 1 are reused
    kpi = values(C, "kpi")[-1]
    assert (kpi["reused"], kpi["sites"], kpi["pruned_sites"], kpi["paths"]) == (17, 545, 544, 2 ** 16 + comb(32, 16))


def test_a_wrong_digit_or_a_coin_that_is_not_unitary_is_refused():
    """D2: the criterion recomputes the step and checks conservation; a changed amplitude is refused,
    and a coin with a² + b² ≠ 1 is refused at its first step, so nothing after slice 0 is recorded."""
    _, C = run("checkerboard")
    i = next(n for n, e in enumerate(C) if e["coord"].get("abstraction") == "step" and e["coord"]["kind"] == "exec"
             and e["payload"]["t"] == 5)
    P, good = C[:i], C[i]["payload"]
    tau = lookups.load(P, C[i]["coord"]["criterion"])
    assert evaluation.judge(P, tau, good)
    bad = dict(good, R=[list(x) for x in good["R"]])
    bad["R"][0] = [bad["R"][0][0] + 1, bad["R"][0][1]]                  # one unit in the last place: 1/5⁵
    assert not evaluation.judge(P, tau, bad)

    from ztes.system.authoring import read_directory
    m = read_directory(PHYSICS / "checkerboard")
    m["constants"] = dict(m["constants"], COIN=[4, 2])                 # a² + b² = 20/25
    system, store = System.from_dict(m), MemoryStore()
    system.plan = system.plan[:3]
    system.run(store, log=quiet)
    D = read(store)
    assert [p["t"] for p in values(D, "step")] == [0] and system.states(D)["step"] == "closed"


def test_monte_carlo_over_paths_meets_the_sign_problem():
    """The same amplitude estimated from 20,000 sampled paths (each path sampled with probability ∝ its
    |weight|, so every sample carries (a + b)ᵀ times a phase): good at T = 4, useless at T = 32, where
    the record has the exact value. The samples are a test, not part of any record."""
    def estimate(T, n, seed):
        rnd, keep, scale, phase = random.Random(seed), float(A / (A + B)), float(A + B) ** T, [1, 1j, -1, -1j]
        acc = [0j, 0j]
        for _ in range(n):
            x, d, turns = 0, 1, 0
            for _ in range(T):
                if rnd.random() >= keep:
                    d, turns = -d, turns + 1
                x += d
            if x == 0:
                acc[0 if d == 1 else 1] += phase[turns % 4]
        return acc[0] * scale / n, acc[1] * scale / n

    def error(T):
        R, L = closed_form(T, 0)
        k = (complex(*map(float, R)), complex(*map(float, L)))
        e = estimate(T, 20000, 1)
        return (abs(e[0] - k[0]) ** 2 + abs(e[1] - k[1]) ** 2) ** 0.5 / (abs(k[0]) ** 2 + abs(k[1]) ** 2) ** 0.5

    assert error(4) < 0.1 and error(16) > 1 and error(32) > 100


# ---- two slits ---------------------------------------------------------------------------------------

def test_two_slits_patterns_differ_by_the_interference_term_only():
    """With the detector the paths through each slit are kept apart; without it their amplitudes add.
    The coherent amplitude is the sum of the two parts, site by site; the totals are equal exactly
    (the parts are orthogonal and the walk unitary); pointwise the patterns differ by 2·Re ψ⁽¹⁾ψ⁽²⁾*."""
    _, C = run("two-slits")
    slices = {(p["t"], len(p["parts"])): p for p in values(C, "step")}
    one, two = slices[(40, 1)], slices[(40, 2)]
    for k in range(len(one["parts"][0]["R"])):
        for f in ("R", "L"):
            u, v = two["parts"][0][f][k], two["parts"][1][f][k]
            assert one["parts"][0][f][k] == [u[0] + v[0], u[1] + v[1]]      # the same scale, 5⁴⁰
    p1, p2 = values(C, "pattern")
    assert (p1["parts"], p2["parts"]) == (1, 2) and p1["total"] == p2["total"]
    cross = []
    for k in range(len(p1["P"])):
        c = Fraction(0)
        for f in ("R", "L"):
            u, v = exact(two["parts"][0][f][k], 5 ** 40), exact(two["parts"][1][f][k], 5 ** 40)
            c += 2 * (u[0] * v[0] + u[1] * v[1])
        assert Fraction(p1["P"][k]) - Fraction(p2["P"][k]) == c
        cross.append(c)
    assert any(cross) and sum(cross) == 0
    kpi = values(C, "kpi")[-1]
    assert (kpi["reused"], kpi["through_permille"], kpi["same_total"]) == (10, 149, True)


def test_two_slits_reuse_the_slices_before_the_screen():
    _, C = run("two-slits")
    keys = [(p["t"], len(p["parts"])) for p in values(C, "step")]
    assert len(keys) == len(set(keys)) == 41 + 31          # experiment 2 starts at the screen, t = 10
    screen = next(p for p in values(C, "step") if p["t"] == 10 and len(p["parts"]) == 1)
    assert Fraction(screen["norm"]) + Fraction(screen["absorbed"]) == 1


# ---- barrier -----------------------------------------------------------------------------------------

def test_barrier_transmission_falls_with_the_width_then_meets_the_over_barrier_part():
    """Exact probabilities beyond the barrier at T = 40: a factor of more than 4 per site of barrier
    while the packet tunnels, then a slower decrease. At T = 40 part of the packet is still inside the
    wider barriers; what remains for W ≥ 3 is mostly the part of the short packet above the barrier."""
    _, C = run("barrier")
    t = [Fraction(x["transmitted"]) for x in values(C, "transmission")]
    assert [x["w"] for x in values(C, "transmission")] == [0, 1, 2, 3, 4]
    assert all(t[k] > t[k + 1] > 0 for k in range(4))
    assert t[0] / t[1] > 4 and t[1] / t[2] > 4 and t[2] / t[3] < 2 and t[3] / t[4] < 2
    assert values(C, "kpi")[-1]["transmitted_ppm"] == [718251, 138690, 24149, 14588, 12218]


@pytest.mark.parametrize("W", [1, 2])
def test_barrier_cut_changes_no_transmitted_value(W):
    """The slices are cut on the left where a site cannot reach x ≥ W by T; the transmitted probability
    equals that of the walk on the whole light cone, without any cut."""
    system, C = run("barrier")
    k = system.definition["constants"]
    M, X0, T = k["M"], k["X0"], k["T"]
    out, inside = (A, B), (Fraction(7, 25), Fraction(24, 25))
    R, z, c = {}, (Fraction(1), Fraction(0)), 1
    for j in range(2 * M + 1):
        R[X0 - M + j] = (c * z[0], c * z[1])
        z, c = cmul(z, (A, B)), c * (2 * M - j) // (j + 1)
    norm0 = sum(v[0] ** 2 + v[1] ** 2 for v in R.values())
    R, L = walk(None, None, R, {}, T, coin=lambda x: inside if 0 <= x < W else out)
    beyond = sum(v[0] ** 2 + v[1] ** 2 for d in (R, L) for x, v in d.items() if x >= W)
    got = next(Fraction(x["transmitted"]) for x in values(C, "transmission") if x["w"] == W)
    assert got == beyond / norm0
