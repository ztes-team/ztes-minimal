# Changelog

Section, theorem and table numbers refer to version 4 of the base paper, *A Calculus of Execution
for Interacting Binary Relations* (https://doi.org/10.20944/preprints202608.1545.v4).

## Unreleased

The code of Z₀ and the ten examples of the paper are unchanged: their records are the same, event
for event (`tests/test_records.py`).

**Physics on the record** (`examples/physics/`, not examples of the paper)
* The model `path-sums` computes Feynman's sum over paths for a relativistic particle on a lattice:
  a discrete-time quantum walk, the unitary form of Feynman's checkerboard. It is computed slice
  by slice in exact arithmetic, as integer numerators over a common denominator. The record is the
  memo table, and conservation of probability is part of the admission criterion. It adds no
  computational power (§4.5).
* `checkerboard`: the free particle. The record equals the sum over all 2¹⁶ paths and a closed
  form. One amplitude at T = 32 is computed on two light cones, reusing the 17 slices of the first
  question.
* `two-slits`: interference, with a which-path detector as a governed change. The two patterns
  have the same total exactly and differ by the interference term only. The slices before the
  screen serve both experiments.
* `barrier`: tunnelling through a mass barrier for five widths, with the probability beyond the
  barrier exact.
* The model `absorbing-walk`: a quantum walk on four nodes with an absorbing trap, in exact
  arithmetic. A dark state gives the classes of Theorem 4: `bright` attains every goal (𝔒); `dark`
  records a certificate, checked without search, that half of the walk never reaches the trap
  (𝔓, Proposition 14); in `dephasing` a compensation event, admissible only after the certificate,
  carries dephasing and the goals the certificate excluded are reached (§6.5, Corollary 9). Tests
  in `tests/test_absorbing.py`.
* `tests/test_physics.py`, with a Monte Carlo baseline that meets the sign problem. The general
  tests (records, replay modes, configurations, workers) cover every system under `examples/`,
  nested ones included.

**Computability on the record** (`examples/computability/`, not examples of the paper)
* The model `halting` executes the modalities of halting, with the evidence for every verdict. Each
  class is stated for the maximal execution of a fixed regime and a named family of goals, of which
  a record is a finite prefix; together the systems show executions in all four classes.
* `machines`: the Busy Beaver champions with 2, 3 and 4 states halt after 6, 21 and 107 steps. A
  cycler and a translated cycler never halt; each has a certificate that the criterion checks
  without search (Proposition 14).
* `collatz`: the numbers 1 … 1,000 reach 1, each by an induction over the record. 5,379 steps are
  recorded instead of 59,542.
* `antihydra`: the recurrence of the six-state machine whose halting is open, 1,000 iterations, no
  verdict.
* `finish-fair`, `finish-unfair`, `finish-unreachable`: tick/finish of §6.2 with a recorded
  scheduler, in classes 𝔗, 𝔚 and 𝔓. The last two carry the same execution payloads and differ in
  the specification of `policy`: the class is a property of the regime.
* `tests/test_halting.py`.
* The model `structural-memoization` (prepared by the co-authors): a transport-damage dispute
  derives a settlement plan, checks it symbolically and publishes it; cold-chain disputes with the
  same reduced funding signature (§5.4, Definition 12) retrieve it through their horizon, bind
  their own evidence and are judged by their own criteria. Eight targets avoid 32 complete plan
  tests. Controls: a contractual exclusion, a stricter certification, a changed planner version
  and an unpublished catalogue. A second system governs a settlement whose fixed cap cannot cover
  the loss and closes the compensation with refunds. The driver `experiment.py` regenerates the
  13 archived records exactly; `tests/test_structural_memoization.py`.
* Its thread, `structural-memoization/thread`: four ordinary systems that share their helpers and
  specifications.
  * `regions`: reuse only within a region of the funding signature and within the precedents that a
    case's policy declares; a control that declares none derives its plan although a matching pattern
    exists; a case above the bound of the rules has no plan.
  * `scaling` and `scaling-pruned`: for k = 2 … 5 tiers a fresh derivation tests 4, 15, 64 and 325
    complete plans (blind planner) or 3, 6, 10 and 15 (pruning planner), and the plan criterion
    checks these counts; a reuse costs one proof in the ontology and one in the criterion.
  * `governed`: a certificate (Proposition 14); a decision of the review board, a separate
    abstraction; a mandate judged by the criterion in force that carries the rules r2 (R1,
    Corollary 9); a pattern of r1 used after the change only by a new proof (revalidation); refunds
    linked to the earlier debits and a closure that needs all of them (§9.3).
  * The history of every abstraction is the same under workers. Each claim of `thread/DESIGN.md` has
    its test in `tests/test_structural_memoization_thread.py`.

* The factorization-patterns experiment publishes a checked residue filter and activates a new
  Fermat search policy under prior authority. Its records show which centers were tested, the
  evidence for each factor and the behavior of a paired control without activation.

* The goldbach-governed-convolution example records every ordered prime pair for a queried sum.
  A governed change restricts one input. Later queries can reuse the unchanged input transform,
  and each result remains verifiable under the rules that produced it.

**Tooling**
* `python -m ztes run` shows a value longer than 600 characters by its beginning and its length; the
  record keeps it whole, and `explain` shows it. The record display of the ten examples is unchanged.
* The CI runs every system under `examples/`, nested ones included.

## 0.1.2 (2026-11-27)

Archived release: https://doi.org/10.5281/zenodo.24608321.

The code of Z₀, every example and every record are unchanged. What changed is what experiment E7
claims, and the wording of two kinds of claims, to agree with the revised text of the base paper.

**Experiment E7**
* E7 is now *What a finite record shows about Theorem 4*. A terminal record shows class 𝔗 or 𝔓.
  Class 𝔒 of `sqrt2-digits` rests on its specification as well, since no window shows that a
  stream never ends. The search of `goldbach` follows one order of checks, so it is in 𝔓 if
  Goldbach's conjecture holds and in 𝔒 otherwise, and never in 𝔚; its window decides neither case.
  0.1.1 read the four classes from the records and placed `goldbach` in 𝔚, which Definition 6 does
  not support. `experiments/run.py e7` prints what each record shows and what it does not; the test
  is now `test_e7_what_a_finite_record_shows`, with the same checks.

**Documentation**
* Theorem 4 classifies execution outcomes (§6.2), and 𝔒 is the correct infinite execution.
* A claim that every lineage has the same history names the fair schedules of Theorem K, and a
  claim from runs names the schedules tested.

## 0.1.1 (2026-11-26)

Archived release: https://doi.org/10.5281/zenodo.24563789.

The code of Z₀ and every recorded example are unchanged: every record is the same, event for event,
as in 0.1.0 (`tests/test_records.py`). What changed is the classification of one defect, one race
in the coordinator of workers, seven experiments, the references to the paper, and the
documentation.

**The paper**
* The base paper is cited by its new title, *A Calculus of Execution for Interacting Binary
  Relations*, and by version 4 of the preprint (Preprints 2026, 2026081545,
  https://doi.org/10.20944/preprints202608.1545.v4), in the README, `CITATION.cff`, `.zenodo.json`,
  `ztes/__init__.py` and the examples.
* The companion paper, *Observable, Governable, Cooperative: Execution Analytics and Adaptive
  Heuristic Agents in the OEE Calculus* (in preparation), is named in the README and in
  `CITATION.cff`.
* Section, table and corollary numbers follow version 4. The main moves: §6.2 → §6.3 (sources of
  non-progress), §6.3 → §6.4 (diagnosis), §6.4 → §6.5 (governed repair), the taxonomy of
  non-termination is §6.2, §3.1.4 → §3.1.2 (lineage of a specification), §9.5 → §9.4. Tables 1 and 2
  of version 4 are the comparison of approaches and the payment example; Corollary 7 is the location
  of nondeterminism, Corollary 8 the genericity of correct executions, Corollary 9 governed
  restoration.
* `aco` and `aco-draw` are now described in the paper (§8.8, Table 8), and their pages say so.

**The defects**
* Case 3 of `python -m ztes defects` (the random generator kept outside the record) now reports what
  is lost as **S1.2**, not R2. Every stored tour still passes its criterion, so every judgment
  replays and R2 holds; what fails is single-valuedness of the realization, which only the full
  replay finds (§8.8, Table 5). `ztes/defects.py` reads this from the judgments-only replay; the
  test `test_each_of_the_eight_deviations_is_found_by_replay` expects it.

**A tenth example**
* `examples/agent`: an agent whose proposals are judged by ethics, ecology and energy, each an
  abstraction with its own criterion; a task is executed only on the three recorded verdicts. It
  executes the conjunctive system criterion of §9.2 (Definition 14) and the compensation of §9.3:
  silence is not consent, a measured overrun is compensated before the next task is judged, and a
  drought changes the water budget by governance. Its record is pinned in `tests/test_records.py`.

**Workers**
* The coordinator of workers (`ztes/system/workers.py`) now adopts the abstractions brought in by
  carried specifications and checks the reports of the workers on one and the same reading of the
  record. Before, it read the record twice; an event that brought in an abstraction could fall
  between the two readings, and the run was judged terminal before the new abstraction had been
  invoked. The decomposition of experiment E6, which brings in dozens of abstractions, showed it in
  one of three runs; the test `test_e6_short_circuit_fixes_the_verdict_and_waiting_fixes_every_lineage`
  now runs it five times. Records under the agenda are unaffected.

**Experiments**
* `experiments/`: seven experiments on control as interacting relations (loops, the end of a stream,
  recursion, demand and cycles, self-similarity, decomposition by specializing the criterion, the
  four fates of Theorem 4), with `experiments/run.py` and `tests/test_experiments.py`. They add no
  code to the model or to Z₀.

**Documentation**
* `REPRODUCING.md`: every result of the paper that comes from this repository, with its command,
  its output and its test.
* `docs/glossary.md`: the terms of the papers next to those of the repository. In particular, the
  paper calls the local outcome Not Yet *Pending* and keeps Not Yet for the status of a goal.
* `docs/tests.md`: the table of tests, moved out of the README.
* README: a "Start here" table, a paragraph on the two relations, how to read the output, a
  current example of output (16 events with the KPI step).
* `docs/specifications-in-execution.md` describes the mechanism as it is, not as a plan.
* The TSP pages say that city 7 is the eighth city: the software numbers cities, like positions,
  from zero.

## 0.1.0 (2026-11-21)

First archived release (https://doi.org/10.5281/zenodo.24416120). Code as in commit 78153ed.

* Z₀ with Axiom 0, τ_root and the store interface (memory, diskcache, Redis); replay under R2 in
  full and judgments-only modes.
* Nine examples: `sqrt2`, `dedekind-cut`, `payment`, `prime-witnesses`, `factorization`, `tsp`,
  `tsp-bnb`, `aco`, `aco-draw`; each record pinned by its length and digest.
* Eight defective mechanisms for the essential conditions of S1 (`python -m ztes defects`).
* Execution by the agenda (`central`) or by one worker per abstraction (`workers`), chosen in the
  configuration (`docs/distribution.md`).
* Specifications carried by a candidate in phase 3 (`docs/specifications-in-execution.md`).
  Before this, the change was prepared in four steps that keep every record identical: hashes and
  times of every example as a baseline; optimizations one per commit (decoders compiled once,
  filtered index, frozen bindings, judgments-only replay); then the carried specifications; then
  the example of adaptive VNS in oee-heuristic-agents that uses them.
* The optional next-prime criterion of `prime-witnesses`.
