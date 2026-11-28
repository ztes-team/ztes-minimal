# Two slits on Feynman's checkerboard: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** Interference, and a which-path detector introduced by a governed
change. The two patterns differ by the interference term only, the total probability is the same
exactly, and the slices before the screen are computed once for both experiments.

## 1. Problem

A particle starts at site 0 moving right, with coin (4/5, 3/5). At T0 = 10 a screen lets only the
sites −4 and 4 through, and the pattern is read at T = 40. In one space dimension the screen acts at
one step of the walk: at T0 it lets two sites through, a two-slit gate in the time of the model
([`../DESIGN.md`](../DESIGN.md), §1). There are two experiments, in sequence:
1. no detector: the amplitudes of the paths through the two slits add;
2. an ideal which-path detector at the slits, with orthogonal detector states: the paths through
   each slit are kept apart, and their probabilities add.

## 2. Decomposition into binary relations

    Step    = { ((t, ψₜ), (t+1, ψₜ₊₁)) : one step of the walk; at t+1 = T0 the screen }
    Pattern = { ((T, ψ_T), P) : P(x) = Σ over the parts of ψ_T of |R(x)|² + |L(x)|² }

A slice holds one or more **parts** on the same sites:
* before the screen, one part;
* after it, one part without the detector, and one part per slit with it.

The tag of a part is the record of the detector; parts never add again.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `step` | Step | the first slice t of the experiment whose key (t, parts) is not recorded, by one step from the recorded slice t − 1; at T0 the screen; ⊥ when all are recorded | the slice is not recorded and has the parts of this experiment; it equals that step exactly; the whole step before the screen has the probability of slice t − 1, and what the screen stops is `absorbed` | `step` |
| `pattern` | Pattern | when slice T is recorded: P at every site and its total; ⊥ before, or once the experiment is answered | P is recomputed from the recorded slice T | `step`, `pattern` |

Payloads: `{"t": 12, "lo": -12, "parts": [{"R": […], "L": […]}], "norm": "…", "absorbed": "0"}`,
and `{"parts": 1, "lo": -40, "P": […], "total": "…"}`. An amplitude [p, q] of slice t stands for
(p + iq)/5ᵗ. Versions 2 of both abstractions reuse the bodies of version 1 with PARTS = 2.

`slices` is a `map` binding over `step`, keyed by (t, number of parts). Before the screen a slice
has one part whatever the detector, so its key is the same in both experiments.

## 4. Design decisions and what they illustrate

* **A detector does not cut paths; it labels them.** Cutting the paths through one slit would give
  the pattern of one slit. The detector instead keeps the two parts apart, so the pattern is the
  sum of their probabilities, P₂ = |ψ⁽¹⁾|² + |ψ⁽²⁾|², instead of P₁ = |ψ⁽¹⁾ + ψ⁽²⁾|².
* **No claim about measurement.** The detector is in place before the particle reaches the screen,
  and the tag is the ordinary which-path bookkeeping. The example makes no claim about collapse or
  about the interpretation of quantum mechanics.
* **A governed change of the experiment (R1).** The detector is `step` v2 and `pattern` v2. Nothing
  before the screen depends on it, so the 10 slices t = 0 … 9 of experiment 1 are reused, and
  `step` v2 starts at the screen.
* **What is exact.**
  * **The totals.** Σ P₁ = Σ P₂ exactly: the two parts are orthogonal and the walk is unitary, so
    the cross term 2·Re ψ⁽¹⁾ψ⁽²⁾* sums to zero over the sites.
  * **Pointwise.** Site by site, P₁ − P₂ is exactly that cross term, and it is not zero.
  * **The amplitudes.** The coherent amplitude is exactly the sum of the two parts at every site.

  The tests check all three from the record.
* **Conservation as a criterion.** At the screen, the probability that passes plus `absorbed`
  equals exactly the probability before it: 568544919552/5¹⁸ ≈ 0.149 passes.

## 5. Plan

```
phase 1, phase 2   step and pattern v1 (no detector)
phase 3            until terminal: 41 slices, then the pattern
govern             step v2, pattern v2 (a detector at the slits: two parts)
phase 3            until terminal: 31 new slices (t = 10 … 40), then the pattern
kpi                execution indicators, once, at the end
```

## 6. Expected end

| Experiment | New slices | Reused | Through the slits | Pattern |
|---|---|---|---|---|
| 1: no detector | 41 | 0 | 0.149 | P₁, with interference |
| 2: a which-path detector | 31 | 10 | the same, exactly | P₂; Σ \|P₁ − P₂\| = 0.292 · Σ P₂ |

The largest pointwise difference is about 15 % of the largest value of P₂. Both abstractions end
in permanent wait. The record has 89 events with the KPI step, and R2 replays it.

## 7. Files

```
system.json                                           types Part, Slice, Pattern; constants COIN, D, T, T0, SLITS; bindings slices, patterns; plan; expect
lib.py                                                helper functions
DESIGN.md
abstractions/step/{criterion, ontology}.v1.py         the bodies
abstractions/step/{criterion, ontology}.v{1,2}.json   PARTS = 1 and 2, same bodies
abstractions/pattern/{criterion, ontology}.v1.py
abstractions/pattern/{criterion, ontology}.v{1,2}.json
abstractions/kpi/{criterion, ontology}.v1.{json,py}   the KPI abstraction; measure() is in lib.py
```

## 8. Execution indicators (KPI)

```
{"profile": 1, "slices": 72, "reused": 10, "through_permille": 149, "same_total": true,
 "interference_permille": 291, "pattern_invocations": 39, "pattern_not_yet": 37}
```

* `through_permille` is the probability that passed the screen, in thousandths.
* `same_total` is true when the two totals are equal, exactly.
* `interference_permille` is Σ |P₁ − P₂| over Σ P₂, in thousandths.
