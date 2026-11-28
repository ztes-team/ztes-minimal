# The absorbing walk from a dark start: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Base paper: Theorem 4, Proposition 14. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** Class 𝔓 with its evidence in the record. The walk starts at node 2, half
of it is in the dark state, and an admitted certificate shows that every goal "absorbed ≥ 1 − 2⁻ᵏ"
with k ≥ 2 is unreachable at every prefix.

## 1. Problem

The walk of `bright`, started at node 2. The specifications are those of `bright`; only the
constant START differs.

## 2. The certificate

`certificate` searches for nodes other than the trap with the same neighbours and finds (2, 3).
Its criterion checks, without search (D2):
* U(e₂ − e₃) = e₂ − e₃ exactly, with the U of its own regime, and the pair avoids node 1;
* Q = 0;
* the dark part p = ⟨d|ρ₀|d⟩/2 = 1/2, recomputed from the start, START = 2;
* the bound 1 − p = 1/2, and k = 2, the least k with 2⁻ᵏ < p.

With Q = 0 every step keeps ⟨d|ρ|d⟩, so at least 1/2 never reaches the trap: absorbed ≤ 1/2 at
every prefix of every continuation. This is an inductive invariant in the sense of Proposition 14.
It holds at the first slice, every admitted step keeps it, and it excludes G₂. G_k is False for
every k ≥ 2 already at the first prefix, so the execution is in 𝔓.

The certificate is a claim about every continuation, checked against the specification of the
step and the start; it reads no slice, and the agenda admits it at the first prefix, before slice 0.
A window of slices with absorbed < 1/2 would show only that no goal is attained yet. R2 replays the
admission of the certificate at its own prefix.

## 3. Plan

```
phase 1, phase 2   step, certificate v1
phase 3            a window of 42 admissions: slices 0 … 40 and the certificate
kpi                execution indicators, once, at the end
```

## 4. Expected end

41 slices and one certificate, `{"pair": [2, 3], "dark": "1/2", "bound": "1/2", "k": 2}`, 53 events
with the KPI step. The dark probability is exactly 1/2 at every slice, and absorbed is below 1/2 at
every slice of the window (0.49999981 at slice 40). No goal is attained. Under workers the
certificate can be admitted at another position, or after the window. R2 replays the record.

## 5. Files

As in `bright`, with START = 2.

## 6. Execution indicators (KPI)

```
{"profile": 1, "slices": 41, "certificates": 1, "absorbed_ppm": 499999, "dark_ppm": 500000, "goals": []}
```
