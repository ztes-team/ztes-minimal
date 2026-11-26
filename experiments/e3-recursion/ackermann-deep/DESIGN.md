# E3. A(3, 7) without a stack: design

*Experiment E3 of [`experiments/README.md`](../../README.md).*

**What this system shows.** The same specifications as [`ackermann`](../ackermann/DESIGN.md), with
the root (3, 7). The value A(3, 7) = 1021 rests on a chain of 1023 recorded premises. Naive
recursion in Python stops at its default limit of 1000 frames with `RecursionError`. Here every
step is a bounded body and the chain is in the record, so depth is limited only by its size.

## Expected end

2558 calls, 2558 values, one result A(3, 7) = 1021: 5124 events, R2 replays them. The run takes
about ten seconds: the ontology of `call` scans the recorded calls, which is a cost of this
specification, not of the model.

## Run

```bash
python -m ztes run experiments/e3-recursion/ackermann-deep
```
