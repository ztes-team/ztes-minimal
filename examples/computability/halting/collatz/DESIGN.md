# Collatz: infinitely many goals, established by an induction over the record: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Base paper: Theorem 4 (a countable family of goals), §4.4.6, §4.4.8. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** A countable family of goals, one per number, each established at a
finite prefix by a finite piece of evidence. The record is the memo table of an induction: the
trajectory of n is followed only until it falls below n, because every smaller number has been
recorded to reach 1.

## 1. Problem

T(n) = n/2 for even n, and 3n + 1 for odd n. The goal 𝒰_n is that the trajectory of n reaches 1.
The numbers are taken in order: n = 1, 2, 3, …. The window is the numbers 1 … 1,000.

## 2. Decomposition into binary relations

    Piece = { ((n, recorded goals), (n, path, below)) : path follows T from n (or from the end of the
              last piece of n) until its first value below n, or for L = 1,000 steps }

## 3. Lifting: the abstraction

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `segment` | Piece | the next piece, for the number read from the last recorded piece | n is that number; every step is T; the piece stops at the first value below n, or after L steps | `segment` |

Payload: `{"n": 27, "path": [27, 82, 41, …, 23], "below": true}`.

## 4. Design decisions and what they illustrate

* **An induction over the record.** When n is checked, every m < n has reached 1, recorded
  earlier. A piece that falls below n therefore establishes that n reaches 1. The rest of the
  trajectory is never computed again: 5,379 steps are recorded, where following every trajectory to
  1 would take 59,542.
* **The next number is read from the record.** It comes from the last recorded piece: the next
  number if that piece fell below its number, the same number otherwise. It is never searched for,
  as ORDER[done] in `tsp`.
* **A bounded body.** A trajectory longer than L would be recorded in pieces, each continuing the
  last. A divergent n would produce pieces forever, and its goal would never be established.
* **What the window shows.**
  * Each goal of the window is established at a finite prefix: this is the affirmative reading of
    §4.4.8.
  * The unbounded run is in 𝔒 if the Collatz conjecture holds. If some n never falls below itself,
    every piece of it stays above n, its goal is False, and the run is in 𝔓.
  * No window decides which, as with `goldbach` in E7.
* **What R2 shows, and what it does not.** R2 replays the judgments the specification made; it does
  not show that the specification is right. An independent arithmetic check found that the
  indicator undercounted when a number needs several pieces (L = 2), and that the criterion did not
  bound a piece that falls below its number. Both were corrected, and the window of 1,000 numbers
  was not affected (`test_collatz_short_pieces_add_up_and_a_piece_has_at_most_L_steps`).

## 5. Plan

```
phase 1, phase 2   segment v1
phase 3            a window of 1,000 admissions: the numbers 1 … 1,000
kpi                execution indicators, once, at the end
```

## 6. Expected end

1,000 pieces, one per number, each falling below its number. The longest piece is that of 703,
which takes 132 steps to fall below 703. 1,009 events with the KPI step; the run is paused, not
terminal. R2 replays the record.

## 7. Files

```
system.json                                           types Piece; constant L; bindings last, pieces; plan; expect
lib.py                                                T, the piece, the next number and piece, measure()
DESIGN.md
abstractions/segment/{criterion, ontology}.v1.{json,py}
abstractions/kpi/{criterion, ontology}.v1.{json,py}   the KPI abstraction
```

## 8. Execution indicators (KPI)

```
{"profile": 1, "numbers": 1000, "recorded_steps": 5379, "steps_to_1": 59542, "saved_permille": 909,
 "longest": 132, "longest_n": 703}
```

`steps_to_1` is read from the record, not computed again: the steps of the piece of n plus those of
the number it falls to.
