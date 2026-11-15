# √2 as a Dedekind cut from three streams, with a governed horizon repair: design (step 0)

*Paper: §8.1–8.5, Table 6. Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** After `sqrt2`: three streams instead of two, and a defect of the design (a wrong horizon) that the termination report exposes and a governed change repairs.

The executable counterpart of §8.1–8.2 (Table 6), §8.4 (Pending versus protective rejection) and
§8.5 (governed horizon repair and R2). Unlike `sqrt2`, which bisects, this is the construction of
the paper: dyadic denominators, integer bounds, and intervals are three separate streams.

## 1. Problem

Construct the intervals Iₙ = [aₙ/dₙ, (aₙ + 1)/dₙ] with dₙ = 2ⁿ and aₙ the integer part of dₙ√2, for
n = 0, …, 4, without any prior evaluation of √2. The interval stream starts with a defective
interface; the defect must be diagnosed and repaired by governance, not by editing the running
system.

## 2. Decomposition into binary relations

    Den  = { (n, (n, 2ⁿ)) : n ≤ 4 }                                       ⊆ ℕ × (ℕ × ℕ)
    Bnd  = { ((n, d), (n, d, a)) : a² ≤ 2d² < (a + 1)² }                    ⊆ (ℕ × ℕ) × ℕ³
    Int  = { ((n, d, a), (n, a/d, (a + 1)/d)) }                            ⊆ ℕ³ × (ℕ × ℚ × ℚ)

Each left component is read from the record (the next index n, the admitted denominator for n, the
admitted bound for n); each right component is the payload of an admitted event.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `denominators` (αN) | Den | {n: k, d: 2ᵏ}, k = number of admitted denominators | n = k, d = 2ⁿ, n ≤ 4 | `denominators` |
| `bounds` (αB) | Bnd | for the admitted denominator of index k: a = isqrt(2d²); ⊥ while it is not admitted | n = k, the denominator is recorded, a² ≤ 2d² < (a + 1)² | `bounds`, `denominators` |
| `intervals` (αD) | Int | for the admitted bound of index k: [a/d, (a + 1)/d]; ⊥ while it is not visible | n = k, exactly one recorded bound for n, lo = a/d, hi = (a + 1)/d | v1: `intervals`, **`bound`**; v2: `intervals`, `bounds` |

Payloads are records: `{"n": 2, "d": 4}`, `{"n": 2, "d": 4, "a": 5}`, `{"n": 2, "lo": "5/4", "hi": "3/2"}`.

**The defect.** `intervals/ontology.v1` reads the lineage `bound` instead of `bounds`. That lineage
is not part of the system, so the ontology never sees a bound. The criterion reads `bounds`
correctly; only the interface of the realization is wrong.

## 4. Design decisions and what they illustrate

* **D1.** The ontology of `bounds` specifies one real number that no finite record contains; each
  invocation resolves it against the admitted index to exactly one integer (§8.2).
* **D2 and §8.4.** `bounds` computes; its criterion checks a² ≤ 2d² < (a + 1)² independently. An
  invocation of `intervals` before its bound is visible is ⊥ (Not Yet), which is different from a
  protective rejection (τ false).
* **Structural non-progress (§6.2, §8.4).** With v1, `intervals` ends in permanent wait on the
  external lineage `bound` while the bounds it needs are already in C. The termination report is
  the diagnosis: the waiting is caused by the interface, not by missing data.
* **Governed repair (§8.5, R1).** `intervals/ontology.v2` declares the correct lineage. It becomes
  active only when its event is admitted under τ_root (S1.3, S1.5); the earlier events stay as they
  were, and the intervals are then built from the bounds admitted before the repair.
* **R2.** Replay verifies the bounds, the absence of intervals before the repair, the repair event,
  and the intervals under v2.

## 5. Plan

```
phase 1, phase 2      v1 of all specifications (intervals with the defect)
phase 3               until terminal: denominators and bounds complete, intervals waits
govern                intervals/ontology.v2 (the repair)
phase 3               until terminal: the five intervals are admitted
```

## 6. Expected end

After the first phase 3: denominators n = 0…4 and bounds a = 1, 2, 5, 11, 22 are admitted;
`denominators` is closed (n = 5 refused); `bounds` waits; `intervals` waits on the external lineage
`['bound']`. After the repair the five intervals of Table 6 are admitted:

| n | dₙ | aₙ | Iₙ |
|---|---|---|---|
| 0 | 1 | 1 | [1, 2] |
| 1 | 2 | 2 | [1, 3/2] |
| 2 | 4 | 5 | [5/4, 3/2] |
| 3 | 8 | 11 | [11/8, 3/2] |
| 4 | 16 | 22 | [11/8, 23/16] |

Final states: `denominators` closed, `bounds` and `intervals` in permanent wait. The record has 23
events of the construction; the KPI step at the end adds 3 (the profile and its specifications), 26
in all, and R2 replays it.

## 7. Files

```
system.json                                   types Den, Bound, Interval; constant N; binding k; plan; expect
DESIGN.md
abstractions/denominators/{criterion, ontology}.v1.json
abstractions/bounds/abstraction.json          bindings den (select one) and dens
abstractions/bounds/{criterion, ontology}.v1.json
abstractions/intervals/{criterion, ontology}.v1.json   ontology v1 has the defect
abstractions/intervals/ontology.v2.json                the repair
```

## 8. Execution indicators (KPI)

The plan ends with one KPI step. The profile it records:

```
denominators: invoked 6, admitted 5, Not Yet 0, false 1
bounds:       invoked 6, admitted 5, Not Yet 1, false 0
intervals:    invoked 9, admitted 5, Not Yet 4, false 0
```

`intervals` is at Not Yet four times. None of these invocations is in the record; only the profile shows that the abstraction was waiting.
