# E6. The same decomposition with contact of order 4: design

*Experiment E6 of [`experiments/README.md`](../../README.md).*

**What this system shows.** A prediction made before the run. The specifications are those of
[`split`](../split/DESIGN.md); only p changes: p(x) = 30 (3x − 1)⁴ + 1, minimum 1 at x = 1/3, contact
of order k = 4. Near 1/3 the interval bound fails on a region of width about ε^{1/k} at resolution
ε, so the number of splits per level should grow as ε^−(1 − 1/k): exponent 3/4 here, against 1/2 for
`split`.

## How the exponent is measured

The least-squares slope of log₂(splits) per level, over the levels from the first third to the last
two: past the coarse start, where every interval fails, and before the cut-off, where the margin of
p ends the refinement. The same rule is used for `split`.

## Expected end

690 splits, 1381 nodes, 691 certified leaves, 690 returns, the root True: 2077 events. Splits per
level 1, 2, 4, 8, 15, 27, 44, 70, 112, 175, 232; exponent 0.75, predicted 0.75. R2 replays the
record. The run takes about a minute under one agenda; it is not run by workers.

## Run

```bash
python -m ztes run experiments/e6-decomposition/split-quartic
```
