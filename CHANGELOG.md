# Changelog

Section, theorem and table numbers refer to version 4 of the base paper, *A Calculus of Execution
for Interacting Binary Relations* (https://doi.org/10.20944/preprints202608.1545.v4).

## 0.1.2 (2026-11-27)

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
