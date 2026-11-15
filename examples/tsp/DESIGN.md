# Travelling salesman by recorded subproblems: design (step 0)

*Paper: §8.8 (exact optimization with recorded subproblems). Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** After `factorization`: reuse at scale, on an NP-hard problem. The record is the memo table of an exact method, across a changed instance and a new question, and the indicators (KPI) measure the saving.

The NP-hardness of the travelling salesman problem is a property of its reduct, the extensional
relation between an instance and its optimal tours, and this example does not change it: the work
per instance is exponential, as in every known exact method. The lifting is a different object: it
computes in phases over the record, and its cost depends on how it uses what is already recorded.
What the calculus changes is what happens to work already done. A conventional solver starts every instance from nothing. Here every solved
subproblem is an admitted, verified event in C; a later instance, a changed instance, or a different
question about the same cities uses those events instead of computing them again. The saving is not
in the size of the problem but in the reuse of what was computed before.

The method is exact (Held–Karp dynamic programming), not a greedy heuristic.

## 1. Problem

Eight cities with integer coordinates, Manhattan distances, city 0 the depot. Answer three questions
in sequence:

1. the shortest tour through cities 0–6;
2. city 7 is added: the shortest tour through cities 0–7;
3. the shortest tour through cities 0, 1, 2, 3, 5, 7 only.

## 2. Decomposition into binary relations

For a set S ⊆ {1, …, N−1} and a city j ∈ S, let cost(S, j) be the length of the shortest path that
starts at 0, visits every city of S exactly once, and ends at j (Held and Karp, 1962):

    cost({j}, j)  = d(0, j)
    cost(S, j)    = min over i ∈ S∖{j} of  cost(S∖{j}, i) + d(i, j)

    Sub  = { ((S, j, recorded costs of S∖{j}), (S, j, cost, pred)) : cost and pred as above }
    Tour = { ((Q, recorded costs of Q), (Q, tour, length)) :
             length = min over j of cost(Q∖{0}, j) + d(j, 0), tour follows the recorded preds }

Sub is the recurrence as a relation: its left side is read from the record (the costs of the smaller
subproblems), its right side is one new recorded subproblem. Sub is multivalued where several
predecessors give the same minimum.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `dp` | Sub | the next subproblem in the fixed order ORDER: **ORDER[done]**, where `done` is the number of recorded subproblems; its cost and pred from the recorded subproblems of S∖{j}; ⊥ when all are recorded | (S, j) is not yet recorded, all its predecessors are recorded, cost is their minimum, pred attains it | `dp` |
| `tour` | Tour | for the query Q: if every cost(Q∖{0}, j) is recorded, the best end j and the tour obtained by following the recorded preds; ⊥ otherwise, or if Q is answered | the tour visits exactly Q, its length is right, and it equals the minimum over the recorded subproblems | `dp`, `tour` |

Payloads: `{"mask": 22, "j": 4, "cost": 21, "pred": 2}` (S as a bitmask), and
`{"cities": […], "tour": [0, …, 0], "length": 38}`. Both bodies are Python functions
(`ontology.v1.py`, `criterion.v1.py`); later versions reuse them with other constants
(`"body_file"`): N, the number of active cities, and Q, the query.

The memo table is a `map` binding over `dp`, keyed by (S, j): `cost` gives the cost, `entry` the
whole subproblem; `done` counts them. Z₀ keeps the map in the index of the record and extends it
with each admitted subproblem, so no invocation rebuilds it. The distance matrix `D` and the order
of the subproblems `ORDER` are derived values, computed once per version from the coordinates;
`dist`, `matrix`, `bits`, `order`, `mask_of`, `follow` and `tour_length` are helpers in `lib.py`.

ORDER sorts the subproblems by the largest city of S, then by |S|. Every predecessor of (S, j)
comes before it, and the order for N − 1 cities is a prefix of the order for N. The recorded
subproblems are therefore always the first `done` entries of ORDER, also after a city is added,
and the next one is read from the record in constant time instead of being searched for.

## 4. Design decisions and what they illustrate

* **The record is the memo table.** Each subproblem is computed once, judged, and recorded. No
  version of `dp` ever recomputes a recorded subproblem: its ontology skips them and its criterion
  refuses them.
* **D1.** Several subproblems are missing at any time, and several predecessors may tie. The
  ontology resolves both by a fixed rule over the record (ORDER[done]; the smallest predecessor
  among the minima). No selector is needed. The criterion does not use ORDER: it admits any
  correct subproblem that is not yet recorded. The order is a policy of the ontology, chosen so
  that the record itself says which subproblem is next.
* **D2: checking, not searching.** The criterion of `dp` reads only the predecessors of one
  subproblem. The criterion of `tour` does not search either: it checks that the tour is a tour,
  that its length is right, and that it equals the minimum over the recorded subproblems. Since
  every subproblem was itself checked when it was admitted, the optimality of the tour is
  established by a chain of local checks that R2 can replay.
* **Governed change of the instance (R1).** Adding city 7 is a new version of `dp` and `tour` with
  N = 8. The subproblems over cities 0–6 depend only on distances between those cities, which do not
  change, so they remain valid and are reused. They are the first 192 entries of ORDER for N = 8;
  only the subproblems that contain city 7 are new, and `dp` v2 continues at ORDER[192].
* **A new question costs no search.** Instance 3 asks about a subset of the cities. Every
  subproblem it needs is already in C; only `tour` runs.

## 5. Plan

```
phase 1, phase 2   dp and tour v1 (N = 7, Q = 0–6)
phase 3            until terminal: 192 subproblems, then the tour
govern             dp v2, tour v2 (N = 8, Q = 0–7): city 7 is added
phase 3            until terminal: 256 new subproblems, then the tour
govern             tour v3 (Q = 0, 1, 2, 3, 5, 7)
phase 3            until terminal: no new subproblem, only the tour
kpi                execution indicators, once, at the end (§8)
```

## 6. Expected end

| Instance | Cities | New subproblems | Subproblems a from-scratch DP needs | Reused | Brute-force tours | Optimal length |
|---|---|---|---|---|---|---|
| 1 | 7 | 192 | 192 | 0 | 360 | 38 |
| 2 | 8 | 256 | 448 | 192 (43 %) | 2,520 | 38 |
| 3 | 6 | 0 | 80 | 80 (100 %) | 60 | 34 |

Over the three questions, 448 subproblems are computed instead of 720 for three independent DP runs.
Adding a city to n cities reuses (n−1)·2ⁿ⁻² of the n·2ⁿ⁻¹ subproblems, close to half for any n; a
question about a subset of solved cities reuses all of them. The optimal lengths agree with an
independent brute-force check (in the tests). Both abstractions end in permanent wait: every
subproblem is recorded and every question answered. The record has 462 events, 468 with the KPI
step (§8 below), and R2 replays it.

The counts are deliberately small so that the run takes a fraction of a second; the point is the
structure of the saving, not the size of the instance. Each invocation costs the same whatever the
size of the record (about 0.1 ms per subproblem up to N = 11, see the README).

## 7. Files

```
system.json                                   types Entry, Tour; constant XY; derived D, ORDER; bindings done, cost, entry, tours; plan; expect
lib.py                                        helper functions
DESIGN.md
abstractions/dp/{criterion, ontology}.v1.py   the bodies, as Python functions
abstractions/dp/{criterion, ontology}.v1.json N = 7
abstractions/dp/{criterion, ontology}.v2.json N = 8, same bodies
abstractions/tour/{criterion, ontology}.v1.py
abstractions/tour/{criterion, ontology}.v{1,2,3}.json   N and Q of the three questions, same bodies
abstractions/kpi/{criterion, ontology}.v1.{json,py}     the KPI abstraction (§8); measure() is in lib.py
```

## 8. Execution indicators (KPI)

The indicators are not part of the calculus but of the design of this execution: two abstractions
above the substrate, admitted by Z₀ like any other and invoked only when they are needed (here once,
by the plan step `{"kpi": true}`). Nothing is computed before it is asked for: admitted events are immutable.

* `profile` (generated for every system) records the outcomes the agenda counted for each abstraction:
  I invocations, A admitted, U ⊥ (Not Yet), of which H by the horizon alone, F τ false. U and F leave
  no event otherwise; its criterion checks what C confirms (A equals the recorded events, I = A + U + F).
  `tour` declares `"requires": {"dp": "NEEDED"}`: of its 227 Not Yet, 224 are decided by counting
  the recorded subproblems, without evaluating its body.
* `kpi` reads the latest profile and the record: `done` (subproblems), `tours` (questions answered).
  `measure()` in `lib.py` gives the indicators of this problem; the criterion checks each against
  its definition.

```
{"profile": 1, "questions": 3, "subproblems": 448, "needed": 720, "saved": 272,
 "tour_invocations": 230, "tour_not_yet": 227}
```

`needed` is what three independent Held–Karp runs need (192 + 448 + 80), `saved` what the record
spared. `tour` is woken after every subproblem, because `dp` is in its horizon, and is ⊥ 227 times:
an indicator of the design of its horizon, visible only here. A heuristic agent can read the `kpi`
lineage like any other and adapt; a new indicator is a new version of `kpi`, a governed change.
