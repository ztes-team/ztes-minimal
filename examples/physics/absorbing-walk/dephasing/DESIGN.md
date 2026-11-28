# The dark walk, then a compensation that adds dephasing: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Base paper: Corollary 9, §6.5, Theorem 4, R1. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** Corollary 9 executed, with the compensation of §6.5 as an admitted
event. The certificate of `dark` is an admitted diagnosis. It makes a compensation admissible, which
carries the change to dephasing, and the goals that the certificate excluded become reachable.

## 1. Problem

The walk of `dark`: slices 0 … 20 under q = 0, with its certificate. A third abstraction,
`compensation`, then decides once. Its decision carries `step` v2 and `certificate` v2, the bodies of
v1 with Q = [1, 4], and the walk continues from the recorded slice 20 under q = 1/4.

## 2. The compensation

| Abstraction | [ω] Ontology: what it proposes | [τ] Criterion: what it admits |
|---|---|---|
| `compensation` | when a certificate is recorded and the walk waits at slice 20: `{"from": 20, "q": [1, 4], "specifications": CHANGE}`; ⊥ before, and after its decision | one decision; a certificate is recorded; `from` is the last recorded slice, 20; 0 < q ≤ 1; it carries exactly the criteria and ontologies of `step` and `certificate`, each with Q = q |

CHANGE names the four files `step/{criterion, ontology}.v2` and `certificate/{criterion, ontology}.v2`
(`{"$specifications": […]}`); the plan does not record them. Z₀ judges the decision with the criterion
of `compensation`, the authority in force, and then each carried specification with τ_root. One event
is appended, and the four versions are active from it on (R1).

**Why the certificate is required.** The criterion admits the change only when the record holds a
certificate. The proof that no continuation of the earlier regime reaches G₂ thus governs what
happens next: the change is admissible because the record shows that the old rules cannot attain
the goal.

**The waits.** `step` v1 proposes nothing after slice 20 until `compensation` has decided, and its
criterion refuses slice 21 before a decision. `compensation` waits for the certificate. Under every
schedule each abstraction then has the history of the agenda: the certificate, slices 0 … 20, the
decision, slices 21 … 60.

## 3. What the change does

Under q = 0 the certificate shows that G_k is unreachable for every k ≥ 2. Dephasing multiplies
every coherence by 3/4 at every step, among them ρ₂₃, which the dark state needs. The invariant
fails, and the dark probability falls towards 0.

Every goal becomes reachable, by an argument that does not depend on the length of the window. Let
Sₜ be the probability that remains after step t. After a step with dephasing, at least the share
q of Sₜ is diagonal, and from node 2, 3 or 4 one step moves at least 16/169 of a diagonal state to
the trap. So Sₜ₊₁ ≤ (165/169)·Sₜ from t = 21 on, and Sₜ → 0 ([`../DESIGN.md`](../DESIGN.md), §2).

In the words of Corollary 9, G₂ is reached along a governed history, at slice 30 (absorbed 0.7438 at
slice 29, 0.7697 at slice 30), although no fixed-regime continuation of the earlier prefix reaches it.
Every judgment before the change, the certificate included, still replays (R2).

## 4. Plan

```
phase 1, phase 2   certificate, step and compensation v1
phase 3            a window of 63 admissions: the certificate, slices 0 … 20,
                   the decision of compensation, slices 21 … 60
kpi                execution indicators, once, at the end
```

There is no `govern` step: the change is an admitted event of phase 3.

## 5. Expected end

61 slices, one certificate, one decision, and 76 events with the KPI step. The payloads of slices
0 … 20 are those of `dark`. G₁ … G₆ are attained at slices 22, 30, 36, 42, 49 and 55. Absorbed is
0.9915 at slice 60, and the dark probability has fallen to 0.0055. The decision carries four
complete specifications, about 21 KB of the record. R2 replays the record.

## 6. Files

As in `dark`, with:
* `abstractions/compensation/{criterion, ontology}.v1.{json,py}`;
* `abstractions/{step, certificate}/{criterion, ontology}.v2.json`: Q = [1, 4], with the bodies of v1,
  carried by the decision;
* `step` v1 with the wait at slice T_DECIDE = 20.

## 7. Execution indicators (KPI)

```
{"profile": 1, "slices": 61, "certificates": 1, "absorbed_ppm": 991545, "dark_ppm": 5466,
 "goals": [22, 30, 36, 42, 49, 55]}
```
