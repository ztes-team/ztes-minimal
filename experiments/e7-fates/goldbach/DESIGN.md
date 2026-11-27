# E7. A search that no window decides: design

*Experiment E7 of [`experiments/README.md`](../../README.md). Base paper: Theorem 4, Definition 6.*

**What this system shows.** A finite observation that decides no class. `check` takes the even numbers n = 4, 6, 8, … in
turn and records the smallest prime p with n − p prime; p = 0 would mean that there is none, and the
criterion then requires a complete check of every q ≤ n/2. `goal` admits once, on a positive atom: a
check with p = 0 is recorded, a counterexample to Goldbach's conjecture.

| Abstraction | [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|---|
| `check` | the next even number and its smallest witness (0: none) | the next number; a correct witness, or a complete check that there is none | own |
| `goal` | the first recorded check without a witness | once; check(n) = 0 is recorded | own, `check` |

No recorded prefix establishes the goal, and no finite record can show that none ever will. By
Definition 6 the status is False at every prefix if Goldbach's conjecture holds, and the execution is
in class 𝔓. Otherwise the one order of checks reaches the first counterexample, `goal` records it,
and the unbounded execution is in class 𝔒. It is never in 𝔚, which needs a branch that keeps the
goal reachable and is never taken. The window of 100 checks decides neither case.

## Expected end

100 checks (n = 4 … 202), no goal: 105 events; the run is paused, not terminal. R2 replays the
record.
