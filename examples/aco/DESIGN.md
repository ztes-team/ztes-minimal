# Ant colony optimization in its natural form: design (step 0)

*Paper: §8.8 and Table 8; this colony is also the sound mechanism against which the eight defects of Table 5 are run (`python -m ztes defects`). Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** After the exact methods: a heuristic. The trail of the ants is a lineage, evaporation is a window, and a quota read from the record replaces the random draw. The result is measured against the exact optimum.

Real ants coordinate through the trail they leave: the environment is a record, and an ant reads
only what is already there. The usual algorithm compresses that record into a mutable pheromone
matrix and replaces the order of events by synchronous iterations. What is lost, order and context,
is then recovered by two devices: evaporation, which multiplies the matrix by (1 − ρ), and a random
draw, which turns one number per edge into a choice. This system puts the method back on a record:

| In the usual algorithm | Here |
|---|---|
| pheromone matrix, updated in place | the lineage `tour` in C; the trail on an edge is computed from recorded tours |
| evaporation: τ ← (1 − ρ)τ | the window of a binding: an ant reads the last K tours |
| random proportional rule | the quota rule: the record keeps the proportions, no draw is made |
| trail × visibility in one formula | trail in [C], visibility in [ω], reinforcement in [τ] |

The companion system `aco-draw` keeps the classical random rule and records every draw, so the two
can be compared on the same cities. Nothing here makes the reduct easier: the system is a
heuristic, and its result is measured against the exact optimum.

## 1. Problem

Twelve cities in the plane (the eight of `tsp` and four more), Manhattan distances. Find a short
closed tour with a budget of T = 60 ants. The optimum, 50, is known from Held–Karp (the method of
`tsp`); a test recomputes it independently.

## 2. Decomposition into binary relations

| Relation | Meaning | Kind |
|---|---|---|
| ant k ↦ walk | the walk ant k takes, given the trail it sees | multivalued: many walks are possible |
| walk ↦ length | the length of the closed tour | function |
| tours ↦ best | the shortest tour found so far | function of the record |

The first relation is the heart of the method. Classically it is resolved by a draw. Here it is
resolved by the record (D1): the same prefix gives the same walk, and different ants walk
differently only because they find different prefixes.

## 3. Lifting: the abstractions

| Abstraction | [ω] candidate | [τ] criterion | Horizon |
|---|---|---|---|
| `tour` | the walk of ant k = number of recorded tours, by the quota rule | k is the next number, k < T, every city once, length correct | `tour` (window K) |
| `best` | the shortest recorded tour, if shorter than the recorded best | valid tour, strictly shorter than the recorded best | `tour`, `best` |
| `kpi` | the indicators of the colony (§8) | each equal to its definition | `tour`, `best`, `profile` |

**The quota rule.** Standing at city i, the ant gives each free city j the same share as the
classical rule: weight(j) / total, with weight = trail(i, j) / distance(i, j)^BETA. Instead of
drawing, it reads from the window how many ants stood at i with j still free (`had`) and how many
of them went to j (`took`), and goes to the city furthest behind its share: the largest
share × (had + 1) − took. Ties go to the nearer city. The proportions that a draw would produce on
average are produced by the record exactly; all arithmetic is rational.

**The trail.** An edge no ant has used has trail 1. Each tour of the window that uses the edge, in
either direction, adds shortest / length, where shortest is the shortest tour of the window. There
is no matrix: the trail is a view of C, recomputed from the K tours an ant reads.

## 4. Design decisions and what they illustrate

- **D1, contextual resolution.** `tour` has no input but the record. Exploration does not come from
  chance; it comes from the fact that every admitted tour changes the context of the next ant.
- **D2, separated admission.** The criterion of `tour` does not know the quota rule. It admits any
  valid tour as experience; whether the tour is good is the business of `best`. The classical
  formula mixes the three roles in one number; here they are three specifications.
- **Evaporation is a horizon, not an update.** `"window": "K"` in the binding `trail` is the whole
  mechanism. Older tours stay in C, immutable (S1.1), and are simply not read. Changing K is a
  change of a specification, hence a governed change under R1; it is not made in this version.
- **`best` reads the lineage, not the latest event.** Axiom 0 does not fix which abstraction is
  invoked next. A `best` that looked at "the latest tour" would miss improvements whenever two ants
  ran between two of its invocations; it therefore reads the shortest recorded tour.
- **Closing.** After T tours the criterion of `tour` is false for every candidate: the lineage is
  closed, not abandoned.

## 5. Plan

Phases 1 and 2 record the specifications; phase 3 runs until the system is terminal; one KPI step.

## 6. Expected end

73 events. `tour` closed (budget), `best` waits. 60 tours, 58 of them distinct cycles. The first
ant walks the nearest-neighbour tour from city 0, of length 54; ant 36 finds a tour of length 52,
which remains the best: 4% above the optimum 50.

Measured, with nothing tuned: BETA = 2 is the customary value and K = N.

| | best of 60 ants | optimum reached |
|---|---|---|
| `aco` (quota, no draw) | 52 | no |
| `aco-draw`, seed 1 (the recorded run) | 54 | no |
| `aco-draw`, seeds 1–40 | 50 five times, 52 twenty-one times, 54 ten times, 56 four times | 5 of 40 |

On this instance the quota colony equals the median run of the random colony. With other windows
the quota colony does reach 50 (for example K = 4), and with others it stays at 54; twelve cities
and one instance support no general claim, and none is made.

## 7. Files

```
system.json                      cities, N, K (window), BETA, T (budget), OPT; types and bindings
lib.py                           distances, tour length, the trail, the quota rule, the indicators
abstractions/tour/               [ω] quota walk   [τ] valid tour within the budget
abstractions/best/               [ω] shortest recorded tour   [τ] strictly shorter than the best
abstractions/kpi/                [ω][τ] indicators, on demand
```

## 8. Execution indicators (KPI)

One KPI step at the end records the profile and the indicators of the colony:

```
tours 60, distinct 58, best 52, found_by_ant 36, optimum 50, gap_permille 40,
tour_invocations 61, best_not_yet 30
```

`tour` is invoked 61 times and admitted 60 times; the 61st invocation is the closing one. `best`
is at Not Yet 30 times: most ants do not improve the best tour, and that leaves no event.
