# Ant colony optimization with recorded draws: design (step 0)

*Paper: §8.8 and Table 8; case 3 of Table 5 removes exactly the recorded draw. Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** After `aco`: the same colony with a real random draw. Chance enters as a boundary abstraction, the only kind of candidate not computed from the record.

The companion of `aco`. Everything is the same (cities, trail, window, budget, criteria) except the
rule by which an ant chooses its next city: here it is the classical random proportional rule. A
random choice is not a function of the record, so the draw cannot be made inside a realization
(S1.2). It enters as what it is: an occurrence from outside, admitted as an event.

## 1. Problem

As in `aco`: twelve cities, Manhattan distances, a budget of T = 60 ants, optimum 50.

## 2. Decomposition into binary relations

| Relation | Meaning | Kind |
|---|---|---|
| draw | N − 1 integers below M, supplied by the environment | not computed from C |
| (ant k, draw k) ↦ walk | the walk of ant k, given the trail it sees and its draw | function |
| walk ↦ length, tours ↦ best | as in `aco` | functions |

Once the draw is an input, the walk is single-valued. The multivalued relation of `aco` has been
split into a boundary occurrence and a function.

## 3. Lifting: the abstractions

| Abstraction | [ω] candidate | [τ] criterion | Horizon |
|---|---|---|---|
| `draw` | boundary: the occurrence of the invocation | fewer than T draws so far, N − 1 integers in [0, M) | `draw` |
| `tour` | the walk of ant k by the random proportional rule with draw k; ⊥ until draw k is admitted | as in `aco` | `tour` (window K), `draw` |
| `best`, `kpi` | as in `aco` | as in `aco` | as in `aco` |

Standing at i, the ant gives each free city the share weight(j) / total and takes the first city at
which the accumulated share exceeds r / M, where r is the next integer of its draw. The comparison
is made on rationals, so the same draw gives the same walk on every machine.

## 4. Design decisions and what they illustrate

- **Chance is a boundary abstraction (§5.2).** `draw` has `"boundary": true` and no body. Its
  occurrences come from the source declared in `system.json` (`"sources"`); the seed belongs to the
  environment, not to any specification. What was drawn is in C.
- **Replay never asks the source.** R2 re-judges every draw and every tour from the record alone.
  A colony that kept its generator outside the record would be the unrecorded input of
  Counterexample 2: the same specifications and the same record could not reproduce a judgment.
- **`tour` waits for its draw.** Ant k uses draw k. Until that draw is admitted the realization is
  ⊥ (Not Yet), and the admission of the draw wakes it: `draw` is in the horizon of `tour`.
- **The budget closes `draw`.** After T draws its criterion is false; `tour` then waits on a
  closed lineage, and the system is terminal.

## 5. Plan

Phases 1 and 2; phase 3 until terminal; one KPI step.

## 6. Expected end

138 events. `draw` closed (budget), `tour` and `best` wait. 60 draws, 60 tours, all distinct. With
seed 1 the best tour has length 54, found by ant 52: 8% above the optimum. Over seeds 1–40 the best
tour is 50 five times, 52 twenty-one times, 54 ten times and 56 four times; the quota colony of
`aco`, which makes no draw, finds 52.

## 7. Files

```
system.json                      as in aco, with M and "sources": the random source of draw
lib.py                           as in aco, with the random proportional rule instead of the quota rule
abstractions/draw/               [ω] boundary   [τ] a well-formed draw within the budget
abstractions/tour/               [ω] walk from the trail and draw k   [τ] valid tour within the budget
abstractions/best/, kpi/         as in aco
```

## 8. Execution indicators (KPI)

```
tours 60, distinct 60, best 54, found_by_ant 52, optimum 50, gap_permille 80,
tour_invocations 61, best_not_yet 28
```

The profile shows `tour` at Not Yet once (invoked before its first draw) and `draw` refused once
(the closing invocation).
