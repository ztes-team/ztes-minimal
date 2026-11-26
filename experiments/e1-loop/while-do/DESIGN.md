# E1. A loop without a loop: design

*Experiment E1 of [`experiments/README.md`](../../README.md). Base paper: Axiom 0, D1/D2 (§1.4), Definition 6.*

**What this system shows.** The language of bodies has no `while` (see `ztes/model/language.py`). A
loop is nevertheless executed: as three relations that read each other only through the record.

## 1. Problem

    x := 27
    while x ≠ 1 do x := (x even ? x/2 : 3x + 1)

The loop runs 111 times (the Collatz orbit of 27 reaches 1 after 111 steps; its largest value is 9232).

## 2. Relations

    Step  = { ((k, x), (k + 1, f(x))) : x ≠ 1 }        the body, f the Collatz map
    Guard = { ((k, x), (k, x ≠ 1)) }                    a predicate on each state
    Exit  = { (k, k) : Guard(k) = false }               the loop ends where the guard says no

## 3. Abstractions

| Abstraction | [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|---|
| `state` | the next state, once the guard has said true of the last one | the position is the next one, guard(k − 1) = true is recorded, x = f(previous x) | `state` (own), `guard` |
| `guard` | the verdict x ≠ 1 of the next recorded state | one verdict per recorded state, and it is correct | `guard` (own), `state` |
| `exit` | the first state of which the guard said false | once, and guard(k) = false is recorded | `exit` (own), `guard` |

Every criterion reads other lineages only through **positive atoms**: "an event with this content is
in C". Its own lineage gives it only its position.

## 4. What it shows

* **Axiom 0 is the loop.** Each step is one admission: the candidate of `state` is appended only if
  its criterion is true on the prefix before it.
* **D2.** The step is proposed by the ontology and judged by the criterion; the criterion recomputes
  f(x) from the recorded previous state and does not trust the proposer.
* **A recorded no.** The loop ends on guard(111) = false, an admitted event: False is a fact in the
  record, not the absence of True (Definition 6 distinguishes False from Not Yet).

## 5. Plan

Phase 1, phase 2, phase 3 until terminal.

## 6. Expected end

112 states (k = 0 … 111, the last x = 1), 112 verdicts (111 true, one false), one exit at k = 111:
232 events. R2 replays them. Under workers, with every schedule, each lineage has the same history.

## 7. Run

```bash
python -m ztes run experiments/e1-loop/while-do
python experiments/run.py e1
```
