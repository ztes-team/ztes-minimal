# Path sums of quantum mechanics on the record: the model (step 0)

*Not an example of the paper. Three systems on the same Z₀: [`checkerboard`](checkerboard/DESIGN.md),
[`two-slits`](two-slits/DESIGN.md), [`barrier`](barrier/DESIGN.md). Tags: [C] epistemic,
[ω] ontological, [τ] eschatological (see [`examples/README.md`](../../README.md)).*

**What this model adds.** A computation from physics, executed and verified on the record. It is
Feynman's sum over paths for a relativistic particle on a lattice, in three canonical cases:
* a free particle, checked against an exact closed form;
* two slits, with and without a which-path detector;
* tunnelling through a barrier.

**A bridge to the theory of algorithms.** The discrete-time quantum walk computed here is also a
bridge between Feynman's path integral and the theory of algorithms. Quantum walks with a coin are
the basis of quantum search algorithms, which find a marked item among N in O(√N) steps (Shenvi,
Kempe and Whaley, Phys. Rev. A 67, 052307, 2003). In a continuous-time, open-system form they model
energy transfer in photosynthetic complexes (Mohseni, Rebentrost, Lloyd and Aspuru-Guzik, J. Chem.
Phys. 129, 174106, 2008). How much quantum coherence contributes to that transfer is still debated
(for example Duan et al., PNAS 2017, https://doi.org/10.1073/pnas.1702261114).

**What it does not claim.** The lifting adds no computational power (§4.5 of the paper). The
systems execute the standard exact method for a discretized path integral: the sum over all paths
is computed slice by slice. This is how Feynman related the path integral to the wave equation. It
is the distributive law: a sum of products over 2ᵀ paths equals a product of T transfer steps.
The hard problems of physics stay where they are:
* the sign problem in many dimensions and for many particles, where one time slice already has
  exponentially many states;
* the continuum limit;
* renormalization.

What the record adds is the subject of this design:
1. **The memo table is the record.** Every slice is computed once, checked, and recorded.
2. **Pruning by an argument only.** A contribution is left out only where it provably cannot
   matter, never because it is small.
3. **Governed changes of the experiment reuse what stays valid.** Examples are a new question about
   a longer time, or a detector at the slits.
4. **Exact arithmetic, replayed bit for bit by R2.** Z₀ accepts no floats in C (`ztes/model/types.py`).
5. **Conservation of probability is part of the admission criterion.**

## 1. The walk

The model is a discrete-time quantum walk on ℤ, the unitary form of Feynman's checkerboard
(Feynman and Hibbs, problem 2-6), with ε = c = ħ = 1. The state at time t is a slice

    ψₜ(x) = (Rₜ(x), Lₜ(x))         the amplitudes moving right and moving left at site x

Each step applies the coin C = [[a, ib], [ib, a]] at every site and then moves R one site to the
right and L one site to the left:

    Rₜ₊₁(x) = a·Rₜ(x−1) + ib·Lₜ(x−1)
    Lₜ₊₁(x) = ib·Rₜ(x+1) + a·Lₜ(x+1)

Here a = COIN[0]/D and b = COIN[1]/D are rational with a² + b² = 1, (4/5, 3/5) in all three
systems. C is then exactly unitary. An amplitude of slice t is (p + iq)/Dᵗ and is recorded as the
pair of integers [p, q]; in `barrier` the scale is D^(M + t). Every probability |R|² + |L|² is an
exact rational. Expanded over paths, the amplitude at (x, T) is

    Σ over direction sequences γ ending at (x, T)  of  a^(T − turns(γ)) · (ib)^turns(γ)
      = aᵀ · Σ_γ (i·εm)^turns(γ),   with εm = b/a = 3/4

This is Feynman's sum (iεm)^R over paths with R turns, normalized by aᵀ.

A barrier is a region where the coin has a smaller a, which is a larger mass. A barrier of
electrostatic type, which is a phase, can let a Dirac particle through (Klein tunnelling), so the
barrier of `barrier` is of mass type.

**Time is a value of the model, not a concept of ZTES.** ZTES has no time. The record is ordered by
admission alone (the position n of an event), no body may read a clock (`ztes/model/language.py`),
and R2 replays without one. The direction is the prefix order of the record; a measure of time is a
choice of the model. If an execution needs a clock, the clock is an abstraction of its own, and
there are many:
* a count of the admitted events of chosen lineages is a logical clock, deterministic and replayed
  by R2, whose rate depends on the density of the events it counts;
* an external clock enters as a boundary abstraction whose readings are recorded as evidence, like
  the draws of `aco-draw`, so replay never asks it;
* the time of a model is a value in the payload, like the step t of a slice here or a recorded
  deadline in `agent`.

The order of the record and the time of a model differ: in `two-slits` the slices t = 10 … 40 of
experiment 2 are admitted after slice t = 40 of experiment 1. Not Yet is a status of a prefix of
the record, not a moment. A wall clock appears only in the infrastructure of distributed runs,
where a service or a worker waits a limited number of seconds for the record; waiting delays a run
and never changes the record.

## 2. Decomposition into binary relations

    Step    = { ((t, ψₜ), (t+1, ψₜ₊₁)) : ψₜ₊₁ = S·C·ψₜ, on the sites the question needs }
    Observe = { ((T, ψ_T), answer) :  probabilities at T, or the probability beyond a barrier }

Both are single-valued: there is no D1 choice in these systems. The extensional relation computed
is the path sum of §1. Step has the same reduct by the distributive law, and the tests check the
equality by enumerating the paths (`tests/test_physics.py`).

## 3. Lifting, shared by the three systems

| Abstraction | Relation | [ω] Ontology: what it proposes | [τ] Criterion: what it admits | [C] Horizon |
|---|---|---|---|---|
| `step` | Step | the first slice of the question that is not recorded, from the recorded slice before it | the slice is not yet recorded; it equals one step of the recorded slice before it, exactly; the whole step has the probability of that slice | `step` |
| an observer (`kernel`, `pattern`, `transmission`) | Observe | the answer, read from the recorded slice T; ⊥ before | the answer is recomputed from the record | `step` and itself |
| `kpi` | – | the indicators of the system | each equals its definition | all |

**One event per time slice.** A slice is one transfer step. The criterion checks the whole step and
the conservation of probability in one judgment, so the record has one event per time step. One
event per site would show ⊥ for every site and allow one worker per site, but it would multiply the
events by the width of the slice.

**Conservation as a criterion.** The criterion of `step` recomputes the step on the whole light cone
and admits the slice only if that step has exactly the probability of the slice before it. The
probability the question leaves out is recorded with the slice:
* in `checkerboard` and `barrier` it is `pruned`, the part cut off (§4);
* in `two-slits` it is `absorbed`, what the screen stops.

A coin that is not unitary (a² + b² ≠ 1) is therefore refused at its first step.

**Exact values.** Every value in C is exact, so R2 reproduces every judgment bit for bit on every
platform, which `math.cos` would not guarantee.
* **Integer numerators.** Amplitudes are recorded as integer numerators over a common denominator,
  so they are read and computed as integers. Written as rationals "p/q", the record of `barrier`
  took almost four times as long to run, much of it spent reading the rationals back.
* **The price is in digits.** With denominator 5 a numerator has about 0.7·t digits after t steps.
  The records are 0.07, 0.21 and 1.4 MB.

`python -m ztes run` therefore shows a long value by its beginning and its length.

## 4. Pruning by an argument only

Outside the forward light cone of the source every amplitude is zero, and an amplitude moves at most
one site per step, so a site cannot influence a site farther away than the number of steps left.
Both facts are inductive invariants of the step, in the sense of Proposition 14:
* **`checkerboard`.** For a question about one amplitude K(X, T), the sites outside the backward
  light cone of (X, T) are cut off.
* **`barrier`.** Only the probability beyond the barrier is asked for, so the sites that cannot
  reach x ≥ W by time T are cut off.

The probability of the sites cut off is recorded (`pruned`), so conservation stays exact. Amplitudes
are never dropped because they are small: in a sum of phases, small terms cancel large ones. The
tests check that every observed value equals that of the walk without any cut.

## 5. Design decisions and what they illustrate

* **The record is the memo table.** The sum over 2ᵀ paths is never formed. Each slice is computed
  once from the recorded slice before it, so each path segment is evaluated once for all the paths
  through it. A slice is keyed by what determines it, so a later question finds the slices that an
  earlier one recorded. This is the counterpart of `tsp`.
* **D2: checking, not summing.** The criterion of `step` knows nothing of paths. It checks one
  transfer step and the conservation of probability against the record. The equality with the
  path sum is a theorem (distributivity), checked by enumeration in the tests.
* **Not Yet (⊥).** An observer is ⊥ until slice T is recorded (`"requires"`), and `step` is ⊥ once
  every slice of its question is recorded.
* **Pruning only by an invariant (§4)**, never by magnitude.
* **Governed changes.** Every question or experiment is a new version of `step` and of the observer:
  * a question about a longer time keeps the recorded slices it needs;
  * a detector keeps the slices before the screen;
  * a wider barrier is a new instance with slices of its own.

## 6. The Monte Carlo baseline

How a sampled estimate of the same sum fares is a test (`test_monte_carlo_over_paths_meets_the_sign_problem`),
not part of any record. The record holds what a criterion can judge, and an estimate with a random
error is not such a value.

The test samples 20,000 paths for the amplitude at (0, T), each with probability proportional to
its |weight|, so every sample carries (a + b)ᵀ = 1.4ᵀ times a phase. The relative error is:

| T | 4 | 8 | 16 | 32 |
|---|---|---|---|---|
| relative error | 2.2 % | 31 % | 2.4 times the value | about 1,600 times the value |

This is the sign problem in its simplest form. The record gives the exact value for every T.

## 7. Outside this model

* **The harmonic oscillator.** In a Dirac walk a quadratic electrostatic potential does not confine
  (Klein), but a position-dependent mass does. The comparison with Mehler's kernel holds only in
  the non-relativistic limit, so it is a numerical check, not an exact one.
* **Two space dimensions, and more than one particle.** For many particles one time slice is
  already exponential, and slice-by-slice memoization stops helping.
* **The continuum limit and renormalization.**

## 8. Files

```
DESIGN.md                    this design of the model
checkerboard/                the free particle: system.json, lib.py, DESIGN.md, abstractions/{step, kernel, kpi}
two-slits/                   two slits and a detector: abstractions/{step, pattern, kpi}
barrier/                     tunnelling: abstractions/{step, transmission, kpi}
```

Every system is self-contained (the house rule of the examples), so each repeats the helpers of the
walk in its own `lib.py`.
