# tick / finish with a fair scheduler: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Base paper: the tick/finish example of §6.2, Theorem 4, §5.2, Principle R. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** The tick/finish example of §6.2, with the scheduler as a recorded
lineage. With a fair scheduler finish is taken, and the run is in 𝔗. Its two companions run the
same abstractions with schedulers that never choose finish:
* [`finish-unfair`](../finish-unfair/DESIGN.md): 𝔚;
* [`finish-unreachable`](../finish-unreachable/DESIGN.md): 𝔓.

## 1. Problem

A decision, 0 for tick and 1 for finish, says which abstraction acts next. Finish is admissible
after an even number of ticks. The goal is a recorded finish.

## 2. Decomposition into binary relations

    Policy = { (prefix, d) : d ∈ {0, 1}, while finish is not recorded }
    Tick   = { ((decisions, ticks), k) : the next decision to act on is 0, and k = ticks + 1 }
    Finish = { ((decisions, ticks), ticks) : the next decision to act on is 1, and ticks is even }

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `policy` | Policy | boundary (§5.2): the occurrence of the scheduler, from the seeded source `{"seed": 6, "size": 1, "below": 2}` | any decision, while finish is not recorded | `finish` |
| `tick` | Tick | the tick the recorded decisions call for | exactly that tick | `policy`, `tick` |
| `finish` | Finish | finish, at the first decision for it that comes after an even number of recorded ticks | exactly that finish | `policy`, `tick`, `finish` |

The decisions are acted on in order. A decision for finish after an odd number of ticks is void,
and the next decision is acted on. The helpers `next_tick` and `next_finish` are in `lib.py`.

## 4. Design decisions and what they illustrate

* **The scheduler is in the record (Principle R).** Which abstraction acts next is a recorded
  decision, so the order of the record is evidence.
* **The decisions do not depend on the schedule.** A source gives one occurrence per invocation,
  also when the occurrence is refused. `policy` therefore admits every well-formed decision while
  finish is not recorded, and the decisions are the occurrences of the source in order, under the
  agenda and under workers.

## 5. Plan

```
phase 1, phase 2   policy, tick and finish v1
phase 3            until terminal
kpi                execution indicators (the profile), once, at the end
```

## 6. Expected end

The decisions are 0, 1, 0, 0, 1, 0, 0, 0, 1:
* the decisions for finish after 1 and after 3 ticks are void;
* finish is taken after 6 ticks;
* `policy` then closes (τ false), and the run is terminal, in class 𝔗.

26 events. Under workers `policy` may record more decisions before finish is recorded; the finish
is the same. R2 replays the record.

## 7. Files

```
system.json                                    types Decision, Tick, Finish; sources; bindings decisions, ticks, finishes; plan; expect
lib.py                                         next_tick, next_finish
DESIGN.md
abstractions/policy/{criterion, ontology}.v1.json
abstractions/tick/{criterion, ontology}.v1.{json,py}
abstractions/finish/{criterion, ontology}.v1.{json,py}
```
