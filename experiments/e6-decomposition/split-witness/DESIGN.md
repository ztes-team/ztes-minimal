# E6. A root of p: return at once, abandon the rest: design

*Experiment E6 of [`experiments/README.md`](../../README.md). Base paper: Corollary 7 (the location of nondeterminism), Principle R.*

**What this system shows.** The specifications of [`split`](../split/DESIGN.md) for
p(x) = 9000 (x − 1/3)² − 9, which is negative near 1/3. A node finds the witness x = 5/16 at depth 3;
its verdict False is returned upward at once (short-circuit), and every node whose ancestor is
decided stops: its work is abandoned. This is variant 3 of the design.

## What it shows

* **The verdict is fixed.** In every schedule tested the root returns False with a witness.
* **The abandoned work is not.** A node stops when it sees a decided ancestor, that is, on the
  absence of a decision a moment earlier: an absence read from the interleaving (Principle R). How
  far the other branches got before they stopped depends on the schedule, so the number of events
  differs from run to run. This nondeterminism is declared and located: in the abandoned work, and
  possibly in the choice among witnesses, never in the verdict (Corollary 7).

The control [`split-witness-full`](../split-witness-full/DESIGN.md) waits for both children instead.

## Expected end

Under one agenda: 21 nodes, 13 splits, 7 certified leaves, one witness, 3 returns: 30 events, the
root False with x = 5/16. By workers the verdict is the same and the number of events varies. R2
replays every record.

## Run

```bash
python -m ztes run experiments/e6-decomposition/split-witness
```
