# E2. The end is recorded: design

*Experiment E2 of [`experiments/README.md`](../../README.md). Base paper: Principle R (§5.2), Theorem K, R2.*

**What this system shows.** A loop over a stream may end only on a recorded fact. The fact is
final because another relation makes every later item inadmissible.

## 1. Problem

    s := 0
    for a in items do s := s + a          items = 5, 3, 8, 1, 9, 2, 7, 4

The sum is 39.

## 2. Relations

    Item = { (k, a_k) : k < 8 }                         the source
    More = { (k, k < 8) }                               is there an item k?
    Fold = { ((k, s), (k + 1, s + a_k)) }               the body
    Result = { (n, s) : More(n) = false, Fold(n − 1) = s }

## 3. Abstractions

| Abstraction | [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|---|
| `items` | the next item of the source | the next position, k < 8, the item of the source | own |
| `more` | true for a recorded item; false at k = 8 | true only of a recorded item; false only where the source admits no item | own, `items` |
| `fold` | the running sum | the next position, item k recorded, s = previous s + a | own, `items` |
| `result` | the sum, once the end is recorded | once; more(n) = false and fold(n − 1) = s are recorded | own, `more`, `fold` |

## 4. What it shows

* **The end is a fact.** more(8) = false is admitted only because the criterion of `items` admits no
  item at k ≥ 8. The absence of a ninth item is final by the interaction of two relations, not by
  waiting.
* **Positive atoms only.** The criterion of `result` reads two recorded facts and nothing else, so its
  judgment stays true on every extension of the record.

The control, [`iteration-absence`](../iteration-absence/DESIGN.md), ends the same loop by reading an
absence.

## 5. Plan

Phase 1, phase 2, phase 3 until terminal.

## 6. Expected end

8 items, 9 verdicts of `more` (the last false), 8 sums, one result (n = 8, s = 39): 35 events. R2
replays them; under workers every lineage has the same history.

## 7. Run

```bash
python -m ztes run experiments/e2-end/iteration
python experiments/run.py e2
```
