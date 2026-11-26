# E3. Recursion: the record is both the memo and the stack: design

*Experiment E3 of [`experiments/README.md`](../../README.md). Base paper: Axiom 0, S1 (one event per call), R1, R2.*

**What this system shows.** Recursion without recursion in any body, and three things it gains with
no added mechanism: no value is computed twice, a later instance continues an earlier one, and depth
is not limited by a stack (the last is shown by [`ackermann-deep`](../ackermann-deep/DESIGN.md)).

## 1. Problem

The Ackermann function, a recursion that is not primitive recursive:

    A(0, n) = n + 1
    A(m, 0) = A(m − 1, 1)
    A(m, n) = A(m − 1, A(m, n − 1))

First A(3, 4) = 125, then, on the same record, A(3, 5) = 253.

## 2. Relations

    Call  = { ((m, n), (m', n')) : (m', n') is demanded by (m, n) }     who needs whom
    Value = { ((m, n), A(m, n)) }                                       the function itself
    Result = { ((M0, N0), A(M0, N0)) }

A call (m, n) with m, n > 0 demands (m, n − 1), and, once A(m, n − 1) = u is recorded, (m − 1, u):
the second demand depends on a recorded value. That is what makes this recursion general.

## 3. Abstractions

| Abstraction | [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|---|
| `call` | the root, then the first call that a recorded call demands and that is not recorded | once per call; the root, or demanded by a recorded call (for the nested call: by a recorded value) | own, `value` |
| `value` | the value of the first recorded call whose premises are recorded | once per call; the call is recorded; the value follows from recorded values | own, `call` |
| `result` | the value of the root, when it is recorded | once per root; value(M0, N0) = v is recorded | own, `value` |

Every criterion reads other lineages only through positive atoms; its own lineage gives it only
uniqueness (a call, a value, a result is recorded once).

## 4. What it shows

* **Memoization.** A value is recorded once and read wherever it is needed: A(3, 4) needs 315
  values, where naive recursion makes 10 307 calls.
* **Continuation.** The governed change makes (3, 5) the root (criteria and ontologies v2: the same
  bodies, N0 = 5). The 315 values of A(3, 4) stay and are part of A(3, 5): it adds 321 values, where
  alone it needs 636.
* **The criterion decides, R1.** The new root enters as new versions of `call` and `result`, under
  the same rule as any other event; R2 replays the record across the change.

## 5. Plan

```
phase 1, phase 2
phase 3          A(3, 4)
govern           call and result v2: the root is (3, 5)
phase 3          A(3, 5)
```

## 6. Expected end

636 calls, 636 values, two results, A(3, 4) = 125 and A(3, 5) = 253: 1285 events. R2 replays them;
under workers every lineage has the same history.

## 7. Run

```bash
python -m ztes run experiments/e3-recursion/ackermann
python experiments/run.py e3
```
