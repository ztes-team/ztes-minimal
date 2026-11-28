# Examples

Ten systems, the executable counterparts of the examples in the base paper *A Calculus of
Execution for Interacting Binary Relations* (version 4, https://doi.org/10.20944/preprints202608.1545.v4),
Section 8 and Table 8. Seven come from its worked examples; two (`aco`, `aco-draw`) apply the same
method to a heuristic, and `aco` is also the colony of the eight defective mechanisms of Table 5.
The tenth, `agent`, executes the conjunctive system criterion of §9.2 (Definition 14), with ethics,
ecology and energy as criteria of their own, and the compensation of §9.3.
[`REPRODUCING.md`](../REPRODUCING.md) gives for each result of the paper the command and the
expected output. Each is a directory of JSON specifications with a `DESIGN.md` that records
the design step by step: the problem, its decomposition into binary relations, the lifting into
abstractions, the design decisions, the plan, the expected end, the files, and the indicators.

The examples contain only specifications: no example adds code to the model or to Z₀. Most bodies
are expressions in JSON; bodies that need loops are one Python function next to the JSON, and
helpers shared by several specifications are in a `lib.py`. Every example is self-contained, so the
two TSP examples and the two ACO examples repeat a few helpers instead of sharing a file.

```bash
python -m ztes check  examples/<name>     # static check
python -m ztes design examples/<name>     # the abstractions; --full shows what is recorded
python -m ztes run    examples/<name>     # execute, show the record and a summary, verify (R2)
python -m ztes defects                    # the ant colony on eight defective mechanisms
```

A guided walk through the package, starting with one invocation of `sqrt2`, is in
[`docs/tour.md`](../docs/tour.md).

## Reading order

Each example adds one thing to the one before it; the first line of every `DESIGN.md` says what.

| | Example | Paper | Table 10 | Abstractions | Events | What it adds |
|---|---|---|---|---|---|---|
| 1 | [`sqrt2`](sqrt2/DESIGN.md) | §8.2 (simplified) | C2, C3 | 2 | 16 | the smallest system: two abstractions, one governed change |
| 2 | [`dedekind-cut`](dedekind-cut/DESIGN.md) | §8.1–8.5, Table 6 | C2, C3 | 3 | 26 | three streams; a wrong horizon found at termination and repaired by governance |
| 3 | [`payment`](payment/DESIGN.md) | §1.1, Table 2 | C1 | 4 | 21 | equal payloads, different grounds; protective refusal |
| 4 | [`prime-witnesses`](prime-witnesses/DESIGN.md) | §8.3 | C1, C4 | 3 | 26 | the record resolves a multivalued relation (10 = 5 + 5, not 3 + 7) |
| 5 | [`factorization`](factorization/DESIGN.md) | §8.7, Table 7 | C1, C6 | 3 | 27 | admitted certificates are reused: checking replaces search |
| 6 | [`tsp`](tsp/DESIGN.md) | §8.8 | C2, C6 | 2 | 468 | exact TSP (Held–Karp); the record is the memo table across instances |
| 7 | [`tsp-bnb`](tsp-bnb/DESIGN.md) | §8.8 | C6 | 3 | 71 | exact TSP by branch and bound; recorded bounds prune; optimality as a recorded proof |
| 8 | [`aco`](aco/DESIGN.md) | §8.8, Table 5 | C2 | 2 | 73 | a heuristic: the trail is a lineage, evaporation a window, a quota replaces the draw |
| 9 | [`aco-draw`](aco-draw/DESIGN.md) | §8.8 | C2 | 3 | 138 | the same colony with a random draw, recorded as a boundary event |
| 10 | [`agent`](agent/DESIGN.md) | §9.2, §9.3 | C1, C2 | 7 | 85 | where ethics is: ethics, ecology and energy judge every proposal of an agent as abstractions of their own; silence is not consent; compensation; a governed norm |

The event counts include the KPI step with which every plan ends. The column Table 10 names the contributions of the paper that the example confirms; one Z₀ executes all ten (C5).

## Where to look

| If you want to see … | look at |
|---|---|
| one invocation of Axiom 0, step by step | `sqrt2`, with `run --trace`, and `docs/tour.md` |
| Not Yet (⊥; Pending in the paper): an abstraction that waits and leaves no event | `sqrt2` (`upper`), `factorization` (`factor`) |
| a false judgment that protects, and one that closes | `payment` (`transfer`); `sqrt2` (`lower`) |
| D1: several valid answers, one admitted, no choice function | `prime-witnesses`, `aco` |
| D2: a criterion that knows nothing of how the candidate was made | `factorization`, `aco` (`tour`) |
| a governed change (R1) and replay across it (R2) | `sqrt2`, `dedekind-cut`, `tsp` |
| a defect of the design, diagnosed and repaired | `dedekind-cut` |
| equal payloads distinguished only by evidence | `payment` |
| reuse of earlier results | `factorization`, `tsp`, `tsp-bnb` |
| a datum that is not computed from the record | `aco-draw` (`draw`), and the KPI `profile` in every example |
| forgetting without changing the record | `aco` (the window of `trail`) |
| indicators computed from the record (KPI) | `tsp`, `tsp-bnb`, `aco` |
| an ethical criterion: consent before a deadline, silence is not consent | `agent` (`ethics`) |
| a system criterion composed of several criteria of their own (Definition 14) | `agent` (`decide`) |
| a consequence measured after an admission, and its compensation (§9.3) | `agent` (`compensate`) |
| what breaks when a condition of S1 is dropped | `python -m ztes defects` |

## What each example shows

| Example | D1 contextual resolution | D2 separated admission | Not Yet (⊥) | τ false | Governed change | Ends |
|---|---|---|---|---|---|---|
| `sqrt2` | which bound moves is decided by the record | criteria change, ontologies stay | the other bound | refinement stops at 1/64 | criteria v2 | closed + wait |
| `dedekind-cut` | one integer bound per index | a² ≤ 2d² < (a + 1)² | intervals before their bound | denominator n = 5 | horizon repair of `intervals` | closed + waits |
| `payment` | – | proposing ≠ admitting | transfer before its check | the third payment | – | closed + waits |
| `prime-witnesses` | witness chosen among visible primes | arithmetic check only | before enough primes | prime 29 | – | closed + waits |
| `factorization` | the last certificate is reused | product, certificates, provenance | factor before its primes | prime 29 | – | closed + waits |
| `tsp` | the next subproblem, read from the record | a subproblem checked from its predecessors | tour before its subproblems | – | a city is added; a new question | waits |
| `tsp-bnb` | best-first among open nodes | any valid shorter tour is accepted | proof before the frontier is closed | – | a city is added; the seed | waits |
| `aco` | the walk of an ant, from the trail it sees | any valid tour is experience | `best` when an ant does not improve | budget of 60 ants | – (K is a governed parameter) | closed + wait |
| `aco-draw` | the walk, once its draw is recorded | as `aco`; a draw is judged like any candidate | `tour` before its draw | budget of 60 draws | – | closed + waits |

## The examples

### sqrt2: √2 by bisection

Two abstractions, `lower` and `upper`, propose the midpoint of the current interval; exactly one of
them is defined in each context. After two admissions a governed change replaces both criteria
(v2 stops at width 1/64) without touching the ontologies. Expected end: bounds 3/2, 5/4, 11/8, 23/16,
45/32, 91/64; `lower` closed on 181/128, `upper` in permanent wait.
The shortest example; start here.

### dedekind-cut: the construction of §8.2 with a horizon repair

Three streams: denominators 2ⁿ, integer bounds aₙ with aₙ² ≤ 2·4ⁿ < (aₙ + 1)², and intervals
[aₙ/2ⁿ, (aₙ + 1)/2ⁿ]. The interval ontology v1 reads a wrong lineage, so after the first execution
the termination report shows `intervals` waiting on the external lineage `bound`, although the
bounds are in the record (§6.3, §8.4; class 𝔓 of Theorem 4). A governed change admits ontology v2 with the correct
horizon (§8.5), and the five intervals of Table 6 follow: [1, 2], [1, 3/2], [5/4, 3/2], [11/8, 3/2],
[11/8, 23/16].

### prime-witnesses: interactions over a prime stream

`primes` certifies primes up to 23. `goldbach` admits one witness for each of 10, 14, 20, choosing
the smallest p among the primes visible at that moment: 10 = 5 + 5 (7 was not yet certified),
14 = 7 + 7, 20 = 3 + 17. `twins` admits (3, 5), (5, 7), (11, 13), (17, 19). Finite witnesses
establish no universal statement; the final permanent wait of `twins` is relative to the bound.

The [governed Goldbach example](computability/goldbach-governed-convolution/README.md) counts
ordered representations in a finite domain and tracks which source revisions support each one.

The [optional next-prime criterion](prime-witnesses/DESIGN.md#optional-next-prime-criterion)
reproduces the governed variant in §8.3 of the paper for both prime witnesses and
factorization. The optional plans record 27 and 28 events respectively.

### factorization: reused certificates (Table 7)

`targets` releases 2,310, 30,030, 510,510, 7,429 one after another; `primes` certifies primes up to
23; `factor` reuses the last certificate through a gcd and factors the cofactor by certified primes
only, waiting while a needed prime is missing. Certificates: h₁ = 2·3·5·7·11, h₂ = h₁·13 (gcd 2,310),
h₃ = h₂·17 (gcd 30,030), h₄ = 17·19·23 (gcd 17 with h₃). The criterion checks the product, the prime
certificates and the provenance without any search.

### tsp: an NP-hard problem, solved once and reused

The NP-hardness of the travelling salesman problem belongs to its reduct and is unchanged; the
example does not reduce the work of one instance below that of exact dynamic programming
(Held–Karp). It shows where the calculus saves: every solved
subproblem cost(S, j) is an admitted, verified event, and no version of the solver ever computes a
recorded subproblem again. Three questions are answered in sequence: the optimal tour through 7
cities (192 subproblems), the same after city 8 is added by a governed change (256 new, 192
reused), and the optimal tour through a subset of 6 cities (0 new, 80 reused). Over the three
questions 448 subproblems are computed instead of 720. The criterion of `tour` certifies optimality
without search, by checking the tour against the recorded subproblems, each of which was checked
when it was admitted. The bodies are Python functions, reused across versions with new constants; the memo table is a
`map` binding kept by Z₀ in the index of the record, and shared logic is in `lib.py`. The
subproblems are recorded in an order in which the order for N − 1 cities is a prefix of the order
for N, so the next subproblem is read from the record (`ORDER[done]`) and every invocation costs the
same, however long the record is.

### tsp-bnb: recorded bounds shorten the search

The companion of `tsp`. Every expansion of the search tree records the lower bounds of its children,
every tour found records an upper bound, and a node whose recorded lower bound reaches the recorded
best tour is never expanded. Optimality is a recorded proof (no open node can beat the best tour),
checked against the record. For 7 cities 34 nodes are expanded instead of 1,237; for 8 cities 14
instead of 8,660. When city 7 (the eighth city; cities are numbered from zero) is added, the search tree of instance 1 is no longer valid (all bounds
change), but its optimal tour, with the new city inserted, seeds the upper bound: 14 expansions
instead of 16. The two TSP examples together show that what carries over between instances depends
on what an abstraction records: DP subproblems almost entirely, a branch-and-bound tree only its
best tour.

### aco: a heuristic on the record

Sixty ants look for a short tour through twelve cities. No pheromone matrix exists: the trail on an
edge is computed from the last K recorded tours (the window of a binding, which is all that
evaporation is here), and an ant chooses its next city by a quota read from the record instead of a
draw. The best tour has length 52, against an optimum of 50 known from Held–Karp. `best` reads the
shortest recorded tour, not the latest, because Axiom 0 does not fix which abstraction runs next.

### aco-draw: the same colony with recorded chance

The classical random proportional rule. A draw is not a function of the record, so it enters as a
boundary abstraction: `draw` has no body, its occurrences come from a seeded source declared in
`system.json`, and each admitted draw is evidence. Replay reads the draws from C and never asks the
source. With seed 1 the best tour is 54; over forty seeds it is 50 five times, 52 twenty-one times,
54 ten times and 56 four times.

### payment: identical payloads, different grounds (§1.1)

Three identical requests a → b, 50. The first passes the fraud check and is transferred. The
second fails, is first refused, and is transferred after a supervisor's override is admitted. The
third fails with no override and is refused; `transfer` is closed. Transfers 1 and 2 have equal
payloads; only the retained evidence in their prefixes distinguishes their grounds, and only that
evidence lets R2 reproduce both judgments.

## Beyond Table 8: physics

[`physics/`](physics/README.md) holds systems outside the ten examples of the paper, on the same Z₀ and
in the same standard form. Its first model, [`path-sums`](physics/path-sums/DESIGN.md), computes
Feynman's sum over paths for a relativistic particle on a lattice. The sum is computed slice by
slice, in exact arithmetic, with the record as the memo table, in three systems:
* `checkerboard`, the free particle, checked against all 2¹⁶ paths and a closed form;
* `two-slits`, interference, with a which-path detector as a governed change;
* `barrier`, tunnelling through a mass barrier.

It adds no computational power (§4.5): it is the standard exact method, made replayable and
governable. Its tests are in `tests/test_physics.py`, listed in [`physics/README.md`](physics/README.md#tests-teststest_physicspy).

Its second model, [`absorbing-walk`](physics/absorbing-walk/DESIGN.md) (§6.5), is a quantum walk on four
nodes with an absorbing trap. A dark state gives the classes of Theorem 4 in a physical system: 𝔒
from one start, 𝔓 with an admitted certificate from another, and the restoration of reachability
by a compensation event, admissible only after the certificate, that adds dephasing (Corollary 9). Its tests are in `tests/test_absorbing.py`.

## Beyond Table 8: computability

[`computability/`](computability/README.md) holds a second branch of systems outside the ten examples
of the paper. Its first model, [`halting`](computability/halting/DESIGN.md), executes the modalities
of halting with the evidence for every verdict. Each class of Theorem 4 is stated for the maximal
execution of a fixed regime and a named family of goals; together the systems show all four:
* `machines`: three Busy Beaver champions halt; two machines never halt, each with a certificate
  checked by the criterion (Proposition 14);
* `collatz`: the numbers 1 … 1,000 reach 1 by an induction over the record;
* `antihydra`: the recurrence of a six-state machine whose halting no one has decided;
* `finish-fair`, `finish-unfair`, `finish-unreachable`: tick/finish of §6.2 with a recorded
  scheduler, in classes 𝔗, 𝔚 and 𝔓. The last two have the same execution payloads.

Its tests are in `tests/test_halting.py`, listed in [`computability/README.md`](computability/README.md#tests-teststest_haltingpy).

The [structural memoization model](computability/structural-memoization/README.md) (§5.4) follows a
settlement graph from its construction in a transport dispute to its use in a different claim.
The experiment measures the search avoided when the second case can read the graph, tests when
the cost of its publication is recovered, and replays the evidence for each admission. Its
[thread](computability/structural-memoization/thread/DESIGN.md) (§5.4, §9.3) puts reuse and governance in one
record: a pattern carries the versions under which it was derived and is used after a governed
change of the rules only by a new proof under the new versions.

The [factorization pattern experiment](computability/factorization-patterns/README.md) (§8.7) follows a
residue filter from the probes that led to its publication through a governed change of search policy.
Paired runs factor the same target and record which candidate centers were tested.

The [Goldbach convolution](computability/goldbach-governed-convolution/README.md) (§8.3) counts the
ordered prime pairs for every sum by a number-theoretic transform and checks the counts by
enumeration. A governed change restricts the second addend; the next answer for 20 has three
witnesses instead of four, the unchanged left transform is reused, and the earlier answer replays
under the rules that admitted it.

## Tests of the examples

Every example states its expected end in `system.json` (`"expect"`); `python -m ztes run` compares
the run with it and reports `Expect  OK`. `tests/test_examples.py` checks the same for all examples
and adds the checks that need more than the final record:

| Test | Checks |
|---|---|
| `test_example_is_well_formed` | `check` passes for every example |
| `test_example_meets_its_expected_end` | the run meets `"expect"`: events, final states, admitted values |
| `test_every_example_replays` | R2 for every example, in-process and over HTTP |
| `test_dedekind_cut_repair` | before the repair `intervals` waits on the external lineage; the repair is recorded before the first interval |
| `test_factor_criterion_rejects_a_false_certificate` | D2: an uncertified factor or a wrong provenance is refused |
| `test_payment_grounds_are_in_the_evidence` | equal payloads; transfer 2 is refused on the same prefix without the override |
| `test_tsp_is_optimal_and_reuses_recorded_subproblems` | the tours agree with brute force; 192, 256, 0 new subproblems; none computed twice |
| `test_tsp_bnb_prunes_by_recorded_bounds` | the proven lengths agree with brute force; 34 and 14 expansions; 16 without the seed |
| `test_aco_tours_are_valid_and_measured_against_the_exact_optimum` | every tour is valid; `best` is the earliest shortest; the optimum constant equals an independent Held–Karp |
| `test_aco_quota_needs_no_draw_and_is_a_function_of_the_record` | two runs of `aco` give the same record; it declares no source |
| `test_aco_draws_are_recorded_and_replay_never_asks_the_source` | sixty admitted draws; replay from C alone; another seed gives another record |
| `test_agent_decides_on_three_recorded_verdicts` | four tasks executed, three refused (an objection, the drought budget, silence); the diesel enters the CO₂; the compensation precedes the next ecological verdict; day 1 judged by ecology v1, day 2 by v2 |
| `test_an_interrupted_run_continues_to_the_same_record` (test_system) | a run cut after any event and started again gives the record of an uninterrupted run |
| `test_each_of_the_eight_deviations_is_found_by_replay` (test_substrate) | the ant colony on eight defective mechanisms |
