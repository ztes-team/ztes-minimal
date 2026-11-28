# The dark walk, then dephasing: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Base paper: Corollary 9, Theorem 4, R1. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** Corollary 9 executed: a governed change restores the reachability of
goals that a certificate excluded in the earlier regime.

## 1. Problem

The walk of `dark` for slices 0 … 20, with its certificate. A governed change then activates
dephasing with strength q = 1/4: `step` v2 and `certificate` v2, the bodies of v1 with
Q = [1, 4]. The walk continues from the recorded slice 20.

## 2. What the change does

Under Q = 0 the certificate shows that G_k is unreachable for every k ≥ 2: no continuation of that
regime reaches it. Dephasing multiplies every coherence by 3/4 at every step, among them ρ₂₃, which
the dark state needs. The invariant fails, and the dark probability falls towards 0. G₂ is attained
at slice 30. In the words of Corollary 9, G₂ is reached along a governed history, although no
fixed-regime continuation of the earlier prefix reaches it. Every judgment before the change,
the certificate included, still replays (R2).

`step` and `certificate` change together, because a regime changes as a whole. `certificate` v1,
left active, would still check Q = 0 in its own specification. `certificate` v2 proposes nothing:
under dephasing there is no invariant to certify.

## 3. Plan

```
phase 1, phase 2   step, certificate v1
phase 3            a window of 22 admissions: slices 0 … 20 and the certificate
govern             step v2, certificate v2 (Q = 1/4)
phase 3            a window of 40 admissions: slices 21 … 60
kpi                execution indicators, once, at the end
```

## 4. Expected end

61 slices and one certificate, before the change, and 77 events with the KPI step. Slices 0 … 20
are those of `dark`, event for event. G₁ … G₆ are attained at slices 22, 30, 36, 42, 49 and 55.
Absorbed is 0.9915 at slice 60, and the dark probability has fallen to 0.0055. R2 replays the
record. Under workers the certificate can be admitted after the change, and then version 2 proposes
none; the windows hold the same numbers of admissions.

## 5. Files

As in `dark`, with `abstractions/{step, certificate}/{criterion, ontology}.v2.json`: Q = [1, 4], with
the bodies of v1.

## 6. Execution indicators (KPI)

```
{"profile": 1, "slices": 61, "certificates": 1, "absorbed_ppm": 991545, "dark_ppm": 5466,
 "goals": [22, 30, 36, 42, 49, 55]}
```
