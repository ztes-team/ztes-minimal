# Travelling salesman by branch and bound over the record: design (step 0)

*Paper: §8.8 (the companion of `tsp`). Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** After `tsp`: the same problem by another exact method. Here the record prunes the search itself, and optimality is a recorded proof.

The companion of `tsp`. There, earlier results shorten *repetition*: solved subproblems are not
computed again. Here, earlier results shorten the *search itself*: every expansion records the
lower bounds of its children, every tour found records an upper bound, and nodes whose recorded
lower bound reaches the recorded best tour are never expanded. Optimality is then a recorded proof,
checked against the record. The NP-hardness of the reduct is unchanged; the saving is in how much
of the search tree the recorded bounds let the system skip.

## 1. Problem

The same eight cities as `tsp` (Manhattan distances, depot 0). Find the optimal tour through cities
0–6, prove that it is optimal; then add city 7 and do the same, using what is recorded.

## 2. Decomposition into binary relations

A node of the search tree is a path from 0, p = (0, c₁, …, cₖ), with its cost and a lower bound on
every tour that extends it.

    Expand = { ((p, U), (p, children of p with cost and bound)) : bound(p) < U }
    Best   = { ((T, U), (T, length T)) : T a tour, length T < U }
    Proof  = { ((F, U, T), (T, U)) : every node of the frontier F has bound ≥ U = length T }

U is the length of the recorded best tour (the upper bound) and F the recorded nodes not yet
expanded. Expand is multivalued, since any open node may be expanded next.

The lower bound of a child p ending at c with remaining cities R is

    cost(p) + min over u ∈ R of d(c, u) + Σ over u ∈ R of min over v ∈ R ∪ {0}, v ≠ u of d(u, v),

admissible because every remaining city is left exactly once on the rest of the tour.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `search` | Expand | the open node with the smallest bound (best first), if its bound is below the recorded best tour; its children with cost and bound | the node is recorded, not expanded, not pruned, and the children with their costs and bounds are exactly right | `search`, `best` |
| `best` | Best | the shortest complete tour among the recorded children, if it improves the recorded best; in v2, first a **seed**: the recorded optimal tour for N−1 cities with the new city inserted where it costs least | a valid tour, its length is right, shorter than the recorded best | `search`, `best` |
| `proof` | Proof | when no open node has a bound below the best tour: the proof, with the number of expansions and of open nodes left | every recorded, unexpanded node has bound ≥ the best length, and the counts are right | `search`, `best`, `proof` |

All payloads carry `n`, the number of cities of their instance, and every binding reads only the
events of the current instance (`"where": "x['n'] == N"`). The bodies are Python functions; the
distance matrix `D` is a derived value, and the computation of children and bounds, the open
nodes and the complete tours are helpers in `lib.py`, used alike by the ontology that expands a
node and by the criterion that checks the expansion.

## 4. Design decisions and what they illustrate

* **Pruning by recorded bounds.** A node is open only while its recorded bound is below the
  recorded best tour. When `best` admits a shorter tour, `search` is evaluated again (it is in its
  horizon) and every node at or above the new bound is pruned at once.
* **D1.** Many open nodes could be expanded next; the ontology takes the one with the smallest
  bound (ties by path). The criterion accepts any open, unpruned node: the order is a policy of the
  ontology, not a condition of admission.
* **D2.** The criterion of `search` checks the children and their bounds without searching; the
  criterion of `best` accepts any valid shorter tour, whatever produced it (the search or a seed);
  the criterion of `proof` checks the frontier in the record.
* **Optimality as a recorded proof.** Each bound was checked when its expansion was admitted, and
  `proof` checks that no open node can beat the best tour. R2 replays the whole argument.
* **What carries over to a new instance.** When city 7 is added, the search tree changes: every node
  has a different set of remaining cities and so a different bound. The recorded nodes of instance 1
  are therefore not reused. The recorded optimal tour is: with city 7 inserted it is a valid tour for
  instance 2 and seeds its upper bound.

## 5. Plan

```
phase 1, phase 2   v1 of all specifications, N = 7
phase 3            until terminal: search, best tour, proof
govern             v2 of all specifications, N = 8; best v2 has the seed
phase 3            until terminal: seed, search, proof
kpi                execution indicators, once, at the end (§8)
```

## 6. Expected end

| Instance | Expansions | Open nodes left (pruned) | Expansions without pruning | Best tour | Proof |
|---|---|---|---|---|---|
| 1: 7 cities | 34 | 69 | 1,237 | 38, found by the search | optimal |
| 2: 8 cities, seeded | 14 | 46 | 8,660 | 38, the seed itself | optimal |

"Expansions without pruning" counts the internal nodes of the full search tree, (N−1)!/(N−1−k)!
summed over k < N−1. Pruning by recorded bounds is the main saving here: 14 of 8,660.

The seed saves less: instance 2 without the seed needs 16 expansions instead of 14. With this lower
bound and best-first order the search finds a good tour quickly anyway; the seed matters more with
weaker bounds or depth-first search. Comparing with `tsp`: dynamic programming reuses its recorded
subproblems across instances almost entirely, branch and bound reuses only the upper bound. Which
recorded results carry over depends on what the abstraction records, and that is a design choice
made in step 0.

The optimal tours agree with `tsp` and with brute force (length 38 for both instances). All three
abstractions end in permanent wait. The record has 65 events, 71 with the KPI step
(§8 below), and R2 replays it.

## 7. Files

```
system.json                                    types Node, Expansion, Best, Proof; constant XY; derived D; bindings; plan; expect
lib.py                                         helper functions: children and bounds, open nodes, leaves
DESIGN.md
abstractions/search/{criterion, ontology}.v1.py
abstractions/best/criterion.v1.py
abstractions/best/ontology.v1.py               search only
abstractions/best/ontology.v2.py               seed, then search
abstractions/proof/{criterion, ontology}.v1.py
abstractions/*/{criterion, ontology}.v{1,2}.json   N = 7, then N = 8
abstractions/kpi/{criterion, ontology}.v1.{json,py}  the KPI abstraction (§8); measure() is in lib.py
```

## 8. Execution indicators (KPI)

As in `tsp`, the indicators are abstractions above the substrate, invoked once at the end: `profile`
records the counted outcomes, and `kpi` reads it together with the recorded proofs.

```
{"profile": 1,
 "instances": [{"n": 7, "expansions": 34, "full_tree": 1237, "open_left": 69},
               {"n": 8, "expansions": 14, "full_tree": 8660, "open_left": 46}],
 "search_invocations": 50, "search_not_yet": 2, "best_invocations": 28, "best_not_yet": 26}
```

`expansions` against `full_tree` is the pruning by recorded bounds; the wake-ups show that `best`
is evaluated after every expansion but improves the bound only twice.
