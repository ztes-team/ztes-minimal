# E4. Only what is demanded is computed: design

*Experiment E4 of [`experiments/README.md`](../../README.md). Base paper: D2, the interaction of two relations.*

**What this system shows.** The criterion of `value` admits a value only for a recorded call. The
call relation therefore cuts the value relation down to what the root needs: pruning by demand, with
no mechanism for it.

## 1. Problem

    f(0) = 1,   f(n) = f(⌊n/2⌋) + f(⌊n/3⌋)          for n = 10⁹

## 2. Abstractions

| Abstraction | [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|---|
| `call` | the root, then the first argument of a recorded call that is not recorded | once; the root, or an argument of a recorded call | own |
| `value` | the value of the first recorded call whose arguments have values | once; the call is recorded; the value follows from recorded values | own, `call` |
| `result` | f(10⁹), when it is recorded | once; value(10⁹) = v is recorded | own, `value` |

## 3. Expected end

242 calls, 242 values, one result f(10⁹) = 18 639 940: 492 events. A table computed bottom-up would
need 10⁹ + 1 entries; naive recursion makes 37 279 879 calls. R2 replays the record; under workers
every lineage has the same history.

## 4. Run

```bash
python -m ztes run experiments/e4-demand/sparse
python experiments/run.py e4
```
