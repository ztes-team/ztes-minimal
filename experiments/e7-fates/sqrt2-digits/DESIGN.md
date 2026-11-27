# E7 (class 𝔒). A stream whose goal is reached at a finite prefix: design

*Experiment E7 of [`experiments/README.md`](../../README.md). Base paper: Theorem 4, the remark on ontological infinity.*

**What this system shows.** An execution that does not end and is not a failure. `digit` proposes
the next decimal digit of √2 (computed exactly with an integer square root) and is always defined, so
the stream never ends. `goal` admits once, on a positive atom: the tenth digit is recorded.

| Abstraction | [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|---|
| `digit` | the k-th digit of √2 | the next position, the exact digit | own |
| `goal` | the goal, once the K-th digit is recorded | once; digit K − 1 is recorded | own, `digit` |

The plan observes a window of 100 admissions. The goal is True at C^16, and the stream is still going
when the window closes. The class 𝔒 needs the specification as well: `digit` is always defined, so
the stream never ends, which no window can show. Infinity belongs to the ontology; it is never
admitted, only continued.

## Expected end

99 digits, one goal (k = 9): 105 events; the run is paused, not terminal. R2 replays the record.
