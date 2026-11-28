# Feynman's checkerboard: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** The sum over paths of a free relativistic particle, computed slice by
slice in the record and checked against the sum over all 2¹⁶ paths and against a closed form.
A second question asks for one amplitude at T = 32. It reuses the slices of the first and needs
only the sites that can reach that amplitude.

## 1. Problem

A particle starts at site 0 moving right. The coin is (a, b) = (4/5, 3/5). There are two questions,
in sequence:
1. every amplitude at T = 16, a sum over 2¹⁶ = 65,536 paths;
2. the amplitude at x = 0, T = 32, a sum over C(32, 16) = 601,080,390 paths.

## 2. Decomposition into binary relations

    Step   = { ((t, ψₜ), (t+1, ψₜ₊₁)) : one step of the walk (../DESIGN.md §1), on the support of the question }
    Kernel = { ((T, ψ_T), P) : P(x) = |R_T(x)|² + |L_T(x)|² on the support at T }

The support of slice t is the light cone of the source, [−t, t]. For question 2 it is cut further
to the backward light cone of (0, 32): [max(−t, t − 32), min(t, 32 − t)]. A site outside it cannot
reach x = 0 by T = 32, at one site per step.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `step` | Step | the first slice t of the question whose key (t, lo, hi) is not recorded, by one step from the recorded slice t − 1, cut to the support; ⊥ when all are recorded | the slice is not recorded; it equals that step exactly; the whole step before the cut has the probability of slice t − 1 | `step` |
| `kernel` | Kernel | when slice T is recorded: P on its sites and their total; ⊥ before, or once the question is answered | P is recomputed from the recorded slice T | `step`, `kernel` |

Payloads: `{"t": 5, "lo": -5, "R": [[0, 0], …], "L": […], "norm": "1", "pruned": "0"}`, and
`{"T": 16, "lo": -16, "hi": 16, "P": […], "total": "1"}`. An amplitude [p, q] of slice t stands for
(p + iq)/5ᵗ; probabilities are rationals written "p/q". All bodies are Python functions, and later
versions reuse them with other constants:
* T and X of the question (`X: null` means every site);
* NEEDED, the number of slices `kernel` waits for.

`slices` is a `map` binding over `step`, keyed by (t, lo, hi). The key is what determines a slice,
so question 2 finds the slices 0–16 that question 1 recorded. The helpers `support`, `initial`,
`transfer`, `probability`, `next_slice`, `kernel` and `measure` are in `lib.py`.

## 4. Design decisions and what they illustrate

* **The record is the memo table.** No slice is computed twice: the ontology skips recorded keys
  and the criterion refuses them. The 2¹⁶ paths of question 1 are never formed. Each of the 289
  sites of the 17 slices is computed once, for all the paths through it.
* **D2: checking, not summing.** The criterion of `step` knows nothing of paths. It recomputes one
  step and checks conservation, so a coin with a² + b² ≠ 1 is refused at its first step. That the slices equal the path sum is checked in the tests by
  enumerating all 65,536 paths, and by the number of paths with a given number of turns:
  * ending right after 2k turns, C(r, k)·C(l−1, k−1);
  * ending left after 2k+1 turns, C(r, k)·C(l−1, k);
  * with r = (T + x)/2 and l = (T − x)/2.
* **Pruning by an argument (question 2).** For t > 16 the support is cut to the backward light cone
  of (0, 32). This leaves out 544 of the 800 sites of the full cone. The probability that the cut
  leaves out is recorded in `pruned`, so the sum of `norm` and every `pruned` stays exactly 1.
* **Reuse across questions (R1).** Question 2 is a governed change: `step` v2 and `kernel` v2 with
  T = 32 and X = 0. Up to t = 16 its support is the whole cone, which are the keys question 1
  recorded, so `step` v2 continues at t = 17.
* **Not Yet.** `kernel` declares `"requires": {"step": "NEEDED"}`. Of its 18 ⊥, 16 are decided by
  counting the recorded slices, without evaluating its body.

## 5. Plan

```
phase 1, phase 2   step and kernel v1 (T = 16, every site)
phase 3            until terminal: 17 slices, then the kernel
govern             step v2, kernel v2 (T = 32, X = 0)
phase 3            until terminal: 16 new slices, then the kernel
kpi                execution indicators, once, at the end
```

## 6. Expected end

| Question | Paths summed | Slices | Sites computed | Reused slices | Answer |
|---|---|---|---|---|---|
| 1: every amplitude at T = 16 | 65,536 | 17 | 289 | 0 | total probability exactly 1 |
| 2: the amplitude at (0, 32) | 601,080,390 | 16 | 256 (544 cut) | 17 | R = −0.101188…, L = 0.071746…·i, P = 0.015386… |

The amplitude at (0, 32) is exactly R = −471194401402419542451/5³¹ and L = 334091759107546632768/5³¹·i.
The closed form in the tests gives the same rationals; 2³² paths cannot be enumerated. Both abstractions end in permanent
wait. The record has 50 events with the KPI step, and R2 replays it.

## 7. Files

```
system.json                                        types Slice, Kernel; constants COIN, D; bindings slices, kernels; plan; expect
lib.py                                             helper functions
DESIGN.md
abstractions/step/{criterion, ontology}.v1.py      the bodies, as Python functions
abstractions/step/{criterion, ontology}.v{1,2}.json   the two questions, same bodies
abstractions/kernel/{criterion, ontology}.v1.py
abstractions/kernel/{criterion, ontology}.v{1,2}.json
abstractions/kpi/{criterion, ontology}.v1.{json,py}   the KPI abstraction; measure() is in lib.py
```

## 8. Execution indicators (KPI)

```
{"profile": 1, "questions": 2, "slices": 33, "sites": 545, "pruned_sites": 544, "reused": 17,
 "paths": 601145926, "kernel_invocations": 20, "kernel_not_yet": 18}
```

* `paths` is the number of paths the two answers sum, 2¹⁶ + C(32, 16).
* `sites` is the number of sites computed.
* `pruned_sites` is the number of sites of the full light cone that were not computed.
* `reused` is the number of slices of question 2 that question 1 had recorded.
