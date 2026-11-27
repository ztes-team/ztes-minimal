# E6 (control). A root of p, every node waits for both children: design

*Experiment E6 of [`experiments/README.md`](../../README.md). Base paper: Theorem K.*

**What this system shows.** The system [`split-witness`](../split-witness/DESIGN.md) with SHORT =
false (variant 1). A node returns only when both children have returned, and then False with the
witness of its leftmost false child. No node reads the absence of a decision, and every node reads a
complete horizon, so every lineage has the same history under every fair schedule (Theorem K). The price
is the work that variant 3 abandons.

## Expected end

79 nodes, 39 splits, 39 certified leaves, one witness, 39 returns: 124 events, the root False with
x = 5/16. By workers every lineage has the same history. R2 replays every record.

## Run

```bash
python -m ztes run experiments/e6-decomposition/split-witness-full
```
