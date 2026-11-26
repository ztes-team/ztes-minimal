# E4. A cycle ends in a quiescent record: design

*Experiment E4 of [`experiments/README.md`](../../README.md). Base paper: Theorem 4 (class 𝔓), Definition 6.*

**What this system shows.** The same specifications as [`sparse`](../sparse/DESIGN.md) for a recursion
whose definition is circular:

    f(0) = f(1) + 1,   f(1) = f(0) + 1

Naive recursion calls itself until the stack overflows. Here a call is recorded once, so the cycle
produces two calls and stops; no value can ever be admitted, because each waits for the other. The
record is finite and quiescent: nothing in it can change.

## What it shows

A quiescent record is terminal, and the goal (a value for the root) is not established in it, so its
status is False and the execution is in class 𝔓 of Theorem 4. The cycle is diagnosed in finite time,
as a permanent wait with a reason ("its horizon is quiescent"), not as a crash.

## Expected end

2 calls, no value, no result: 9 events (the other 7 are the genesis event and the six specifications). Every abstraction is in permanent
wait. R2 replays the record.

## Run

```bash
python -m ztes run experiments/e4-demand/cycle
```
