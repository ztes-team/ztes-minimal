# counter: design (step 0)

A test system for the substrate. It exercises the generic context (`count`, `all` with `where`),
record-typed payloads, closing criteria, and a wait on an external lineage.

## 1. Problem

Count from 1 to 5. Keep a running summary (how many and what sum) of the even counts. Double a
sensor reading when one arrives.

## 2. Decomposition into binary relations

    Tick  = { (k, k + 1) : k < 5 }                               ⊆ ℕ × ℕ        k = number of ticks so far
    Evens = { (E, (|E|, ΣE)) : E nonempty }                     ⊆ 𝒫fin(ℕ) × ℕ²  E = even ticks so far
    Alarm = { (v, 2v) : v reading of the sensor, 2v > 0 }        ⊆ ℤ × ℤ

## 3. Lifting: the abstractions

| Abstraction | Relation | Ontology Sω | Criterion Sτ | Horizon |
|---|---|---|---|---|
| `tick` | Tick | n + 1, with n = count of `tick` | w = n + 1 and w ≤ 5 | `tick` |
| `evens` | Evens | {count, sum} of all `tick` values with x even; ⊥ while there are none | the count grows by one and the sum grows | `tick`, `evens` |
| `alarm` | Alarm | 2v, with v = last `sensor`; ⊥ while there is none | w > 0 | `sensor` (external) |

## 4. Design decisions

* `tick` closes itself: its candidate 6 is refused by τ.
* `evens` is idle until an even tick exists, and is refused when its summary would not change.
* `sensor` is not part of the system, so `alarm` waits on an external lineage.

## 5. Plan

No plan: phase 1, phase 2, phase 3 until terminal.

## 6. Expected end

`tick` admits 1…5 and is closed. `evens` admits {1, 2} and {2, 6} and is closed. `alarm` is in
permanent wait on the external lineage `sensor`. The record has 14 events and R2 replays it.

## 7. Files

```
system.json
DESIGN.md
abstractions/{tick, evens, alarm}/{criterion, ontology}.v1.json
```
