# Tunnelling through a mass barrier: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** Tunnelling, computed exactly: the probability that a packet passes
through a region where it has no propagating mode, for five widths of that region. The question
asks only for the probability beyond the barrier, so the sites that cannot reach it are cut off.

## 1. Problem

Outside the barrier the coin is (4/5, 3/5). On the barrier, the sites 0 … W − 1, it is
(7/25, 24/25): a smaller a, a larger mass.

The packet is R(x) = C(16, j)·zʲ at x = −20 + j (j = 0 … 16), with L = 0:
* a binomial envelope, close to a Gaussian, centred at −12;
* the phase z = (4 + 3i)/5 moves it to the right.

Its frequency lies in the gap of the barrier, where |cos ω| > 7/25, so inside it has only decaying
modes. The question is the probability beyond the barrier, x ≥ W, at T = 40, as a fraction of the
packet, for W = 0, 1, 2, 3, 4.

## 2. Decomposition into binary relations

    Step         = { ((t, ψₜ), (t+1, ψₜ₊₁)) : one step of the walk with the coin of each site, on the support }
    Transmission = { ((T, ψ_T, ψ₀), p) : p = Σ_{x ≥ W} |ψ_T(x)|² / Σ_x |ψ₀(x)|² }

The support of slice t is the light cone of the packet, cut on the left at W − (T − t): a site
further left cannot reach x ≥ W by time T, at one site per step. Slice T therefore holds exactly
the sites x ≥ W.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `step` | Step | the first slice (W, t) that is not recorded, by one step from the recorded slice (W, t − 1), cut to the support; ⊥ when all are recorded | the slice is not recorded; it equals that step exactly; the whole step before the cut has the probability of slice t − 1 | `step` |
| `transmission` | Transmission | when slice (W, T) is recorded: its probability over that of slice (W, 0); ⊥ before, or once this width is answered | the fraction is recomputed from the record | `step`, `transmission` |

Payloads: `{"w": 2, "t": 7, "lo": -27, "R": […], "L": […], "norm": "…", "pruned": "…"}`, and
`{"w": 2, "T": 40, "transmitted": "…"}` (an exact rational). An amplitude [p, q] of slice t stands
for (p + iq)/25^(8 + t): the coins are numerators over D = 25, (20, 15) and (7, 24), and the packet
starts over 25⁸ = 5¹⁶. Versions 2–5 reuse the bodies of version 1 with W = 1 … 4.

## 4. Design decisions and what they illustrate

* **A mass barrier, not an electrostatic one.** A barrier of electrostatic type (a phase) lets a
  Dirac particle through (Klein tunnelling). A region of larger mass has a gap, and a wave whose
  frequency lies in it decays inside.
* **Pruning by the question.** Only the probability beyond the barrier is asked for, so the
  reflected part of the packet is cut off as soon as it can no longer come back. Of the 11,685
  sites of the light cones, 4,963 (42 %) are not computed. Their probability is recorded in
  `pruned`, so conservation stays exact.
* **A short packet, so the record stays small.** With 17 sites the packet is short, so part of it
  lies outside the gap and passes over the barrier. Transmission therefore first falls by a factor
  of about 5 per site, which is tunnelling, and then more slowly.

  At T = 40 about 1 % of the packet is still inside the wider barriers, so the values for W = 3 and
  4 are not yet final. At T = 160 (a float check outside the record) the transmission settles near
  1.7 % for W ≥ 3. That is the part of the packet above the barrier: 5 % of the packet lies where
  the barrier has propagating modes.

  A float calibration with a longer packet (width about 12 sites) and a lighter particle outside
  shows the exponential over ten decades, down to 4.7·10⁻¹⁰ at W = 12. But its exact record would be
  tens of MB, too large for an example.
* **Every width is an instance of its own.** It is a governed change of `step` and `transmission`.
  Only the five slices before the packet's cone reaches the barrier would be the same for every
  width, so the key (W, t) does not try to share them.
* **Exact small numbers.** The transmitted probability is an exact rational at every width; the
  KPI shows it in parts per million.

## 5. Plan

```
phase 1, phase 2   step and transmission v1 (W = 0, no barrier)
phase 3            until terminal: 41 slices, then the transmission
govern             step v2, transmission v2 (W = 1); phase 3
govern             … v3 (W = 2), v4 (W = 3), v5 (W = 4); each followed by phase 3
kpi                execution indicators, once, at the end
```

## 6. Expected end

| W | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| beyond the barrier at T = 40 | 0.718 | 0.139 | 0.0241 | 0.0146 | 0.0122 |
| ratio to the next | 5.2 | 5.7 | 1.7 | 1.2 | |

The tests check these values against the walk without any cut, exactly. Both abstractions end in
permanent wait. The record has 237 events with the KPI step (1.4 MB), and R2 replays it.

## 7. Files

```
system.json                                                types Slice, Transmitted; constants OUT, IN, D, PHASE, M, X0, T; bindings slices, transmitted; plan; expect
lib.py                                                     helper functions
DESIGN.md
abstractions/step/{criterion, ontology}.v1.py              the bodies
abstractions/step/{criterion, ontology}.v{1–5}.json        W = 0 … 4, same bodies
abstractions/transmission/{criterion, ontology}.v1.py
abstractions/transmission/{criterion, ontology}.v{1–5}.json
abstractions/kpi/{criterion, ontology}.v1.{json,py}        the KPI abstraction; measure() is in lib.py
```

## 8. Execution indicators (KPI)

```
{"profile": 1, "widths": [0, 1, 2, 3, 4], "transmitted_ppm": [718251, 138690, 24149, 14588, 12218],
 "slices": 205, "sites": 6722, "pruned_sites": 4963,
 "transmission_invocations": 110, "transmission_not_yet": 105}
```
