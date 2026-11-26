# E2 (control). The end read from an absence: design

*Experiment E2 of [`experiments/README.md`](../../README.md). Base paper: Principle R (§5.2), Theorem K, R2.*

**What this system shows.** What goes wrong when a criterion admits on an absence. It is the system
[`iteration`](../iteration/DESIGN.md) without `more`: `result` admits the sum as soon as `fold`
has caught up with `items`, that is, when no further item is recorded *yet*.

## 1. Abstractions

`items` and `fold` as in `iteration`. `result`:

| [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|
| the last sum, when there are as many sums as items | once; the number of sums equals the number of items | own, `items`, `fold` |

The criterion counts the items recorded so far. A count is not a positive atom: it can be true on a
prefix and false on its extension.

## 2. What it shows

* **Principle R.** An absence ("no ninth item is recorded") is read from the interleaving of the
  record. Under one agenda `result` is admitted after the first item, with s = 5. By workers the
  producer is usually faster and the sum is 39. The history of `result` depends on the schedule:
  Theorem K does not hold for this design.
* **R2 cannot see it.** Every judgment was true on its own prefix, so the replay passes in every run.
  The defect is in the design of the criterion, and only Principle R excludes it.

## 3. Expected end

Under one agenda: 8 items, 8 sums, one result (n = 1, s = 5): 24 events, and R2 replays them. By
workers the result is usually n = 8, s = 39; it is not fixed.

## 4. Run

```bash
python -m ztes run experiments/e2-end/iteration-absence
python experiments/run.py e2
```
