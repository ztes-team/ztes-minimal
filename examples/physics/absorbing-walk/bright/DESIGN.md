# The absorbing walk from a bright start: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Base paper: Theorem 4. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** An unconditional, executed class 𝔒. The walk starts at node 4, which
has no part in the dark state, and every goal "absorbed ≥ 1 − 2⁻ᵏ" is attained at a finite slice.

## 1. Problem

The square 1–2–4–3–1 with the trap at node 1, the Crank–Nicolson step with ε = 1/3 (D = 13), no
dephasing (Q = 0), and the start at node 4. The goals are G_k: "a slice with absorbed ≥ 1 − 2⁻ᵏ is
recorded", k = 1, 2, … .

## 2. Why every goal is attained

The component of the walk along the dark state d = e₂ − e₃ is 0 at the start and stays 0. On the
rest, the step with absorption has the eigenvalues 0 and (7 ± 2√17·i)/13, with |λ|² = 9/13
([`../DESIGN.md`](../DESIGN.md), §2). The probability that remains falls roughly as (9/13)ᵗ, so every
G_k is attained at a finite slice. `step` has no bound, so the unbounded execution is infinite and
in 𝔒. The window of 41 slices shows G₁ … G₂₁.

`certificate` finds the pair (2, 3), but the start has no dark part (p = 0), so it proposes nothing:
it stays ⊥, and no certificate is needed.

## 3. Plan

```
phase 1, phase 2   step, certificate v1
phase 3            a window of 41 admissions: slices 0 … 40
kpi                execution indicators, once, at the end
```

## 4. Expected end

41 slices and no certificate, 52 events with the KPI step. Absorbed at slice 40 is 0.99999957. The
first slices of G₁, G₂, … are 2, 5, 6, 9, 10, 13, 14, 16, 17, 20, 21, 24, 25, 27, 28, 31, 32, 35,
36, 39, 40. The run is paused, not terminal. R2 replays the record.

## 5. Files

```
system.json                                          types Slice, Certificate, Kpi; constants A, EPS, D, TRAP, START; derived U; plan; expect
lib.py                                               the walk: cayley, next_slice, darkness, twins, certify, measure
DESIGN.md
abstractions/step/{criterion, ontology}.v1.{json,py}
abstractions/certificate/{criterion, ontology}.v1.{json,py}
abstractions/kpi/{criterion, ontology}.v1.{json,py}
```

## 6. Execution indicators (KPI)

```
{"profile": 1, "slices": 41, "certificates": 0, "absorbed_ppm": 999999, "dark_ppm": 0,
 "goals": [2, 5, 6, 9, 10, 13, 14, 16, 17, 20, 21, 24, 25, 27, 28, 31, 32, 35, 36, 39, 40]}
```

* `absorbed_ppm` and `dark_ppm` are the absorbed and the dark probability at the last slice, in
  millionths.
* `goals` lists the first slice of each G_k recorded.
