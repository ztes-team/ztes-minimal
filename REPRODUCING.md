# Reproducing the results of the papers

This page lists every result of the base paper that comes from this repository. For each it gives
the command that produces it, what the command prints, and the test that checks it. Section, table
and theorem numbers refer to version 4 of the base paper, *A Calculus of Execution for Interacting
Binary Relations* (Preprints 2026, 2026081545, https://doi.org/10.20944/preprints202608.1545.v4).
The examples of the companion paper, *Observable, Governable, Cooperative: Execution Analytics and
Adaptive Heuristic Agents in the OEE Calculus* (in preparation), are reproduced in
[oee-heuristic-agents](https://github.com/ztes-team/oee-heuristic-agents/blob/main/REPRODUCING.md).

```bash
pip install -r requirements.txt          # Python 3.12 or later
python -m pytest -q                      # every check below, in about a minute
```

Every `run` ends with `R2  replay of N events: OK` (the whole record replayed from the empty prefix)
and `Expect  OK` (the end stated in `system.json` holds). Under the agenda every record is the same
on every machine; `tests/test_records.py` pins each one by its number of events and a digest.

## What the executions confirm, and what they do not

The theorems are proved in the paper. The executions confirm, on these instances, four things:
the construction is realizable, every judgment replays from the empty prefix, a violated
safeguard is detected, and results determined by their inputs do not depend on the schedule. They
make no claim of speed. Where an execution shows an infinite object, it shows a finite prefix of it.

## The examples of Section 8 and Table 8

| Paper | Command | What it prints | Test |
|---|---|---|---|
| §8.2, Table 6: dyadic intervals for √2 | `python -m ztes run examples/dedekind-cut` | the intervals [1, 2], [1, 3/2], [5/4, 3/2], [11/8, 3/2], [11/8, 23/16]; 26 events | `test_example_meets_its_expected_end` |
| §8.2 (simplified): bisection for √2 | `python -m ztes run examples/sqrt2` | bounds 3/2, 5/4, 11/8, 23/16, 45/32, 91/64; `lower` closed on 181/128, `upper` in permanent wait; 16 events | `test_sqrt2_termination_states` |
| §8.3: prime witnesses | `python -m ztes run examples/prime-witnesses` | under the agenda 10 = 5 + 5, 14 = 7 + 7, 20 = 3 + 17; twins (3, 5), (5, 7), (11, 13), (17, 19); 26 events | `test_example_meets_its_expected_end` |
| §8.3: 3 + 7 in another execution | `python -m ztes run examples/prime-witnesses --workers` | under some schedules 10 = 3 + 7, because 7 is already recorded when `goldbach` is invoked (`docs/distribution.md`) | `test_every_example_under_random_schedules` |
| §8.4: the interface defect | `python -m ztes run examples/dedekind-cut` | after the first execution: `intervals permanent wait (Not Yet): waits on external ['bound']` and the diagnosis | `test_dedekind_cut_repair` |
| §8.5: governed horizon repair, R2 across it | the same run | ontology v2 of `intervals` is recorded before the first interval; R2 replays every event, those before the repair under v1 | `test_dedekind_cut_repair` |
| §8.7, Table 7: factorization by reused certificates | `python -m ztes run examples/factorization` | h₁ = 2·3·5·7·11, h₂ = h₁·13, h₃ = h₂·17, h₄ = 17·19·23; 27 events | `test_factor_criterion_rejects_a_false_certificate` |
| §8.8: Held–Karp over three questions | `python -m ztes run examples/tsp --metrics` | 192, 256 and 0 new subproblems; `"subproblems": 448, "needed": 720`; 468 events | `test_tsp_is_optimal_and_reuses_recorded_subproblems` |
| §8.8: the 230 evaluations of `tour` | the same run | `tour  230  3  227  224  0`: 230 invocations, 3 admitted, 227 Pending, of which 224 stop before the body runs, no false judgment | `test_tsp_kpi_measures_reuse_on_demand` |
| §8.8: branch and bound | `python -m ztes run examples/tsp-bnb --metrics` | 34 expansions of 1,237 internal nodes for seven cities, 14 of 8,660 for eight (16 without the seed); length 38; 71 events | `test_tsp_bnb_prunes_by_recorded_bounds` |
| §8.8: Ant System with a quota | `python -m ztes run examples/aco --metrics` | 60 tours, best 52 against the optimum 50; 73 events | `test_aco_tours_are_valid_and_measured_against_the_exact_optimum` |
| §8.8: Ant System with recorded draws | `python -m ztes run examples/aco-draw --metrics` | 60 admitted draws, best 54 with seed 1; 138 events | `test_aco_draws_are_recorded_and_replay_never_asks_the_source` |
| §1.1, Table 2: two payments, equal payloads | `python -m ztes run examples/payment` then `python -m ztes explain DIR N` | transfers 1 and 2 have equal payloads and different grounds; the third is refused; 21 events | `test_payment_grounds_are_in_the_evidence` |
| §9.2 (Definition 14), §9.3: ethics, ecology and energy as criteria of their own | `python -m ztes run examples/agent` | T1–T4 executed; T5 refused (an objection), T6 (the drought budget, 70 > 60 m³), T7 (no answer before the deadline); 15 m³ compensated for T3; 85 events | `test_agent_decides_on_three_recorded_verdicts` |

`--record DIR` keeps the record; `python -m ztes explain DIR N` shows the ground of event N, and
`python -m ztes verify DIR` replays a kept record. Positions are numbered from zero here and from one
in the paper (§4.1.2): position k in the output is position k + 1 in the paper.

## The eight safeguards (Table 5, Theorems C, C′ and D)

```bash
python -m ztes defects
```

runs the ant colony on a sound mechanism (73 events, replay OK) and on eight defective ones. The
full replay stops every defective record. The replay of judgments (`verify --judgments`) stops
seven; it misses case 3, whose draws were never recorded. There every stored tour still passes its
criterion, so R2 holds, and what fails is single-valuedness of the realization (S1.2), which only
the full replay checks (§8.8).

| | Safeguard | Full replay stops at | Lost |
|---|---|---|---|
| 1 | append-only (S1.1) | event 9 of 19: the realization no longer matches the record | R2 |
| 2 | shared order (S1.1) | event 20 of 21: criterion version not active | R1 |
| 3 | recorded inputs (S1.2) | event 7 of 20: the realization is ⊥, the record has a tour | S1.2 |
| 4 | immutable versions (S1.3) | event 3 of 19: specification address | R2 |
| 5 | endogenous activation (S1.3) | event 19 of 20: ontology version not active | R1 |
| 6 | retained evidence (S1.4) | event 5 of 19: the realization no longer matches the record | R2 |
| 7 | certification (S1.5) | event 67 of 68: criterion is false on replay | R2 |
| 8 | record, then activate | event 19 of 21: criterion version not active | R1 |

Tests: `test_each_of_the_eight_deviations_is_found_by_replay`,
`test_the_faster_mode_finds_every_defect_but_the_hidden_draw`.

## Schedules and failures (Theorem K, Corollary 7)

```bash
python -m ztes run examples/factorization --workers     # one worker per abstraction
python -m pytest -q tests/test_workers.py               # random schedules and killed workers
```

Under every schedule tested, every record replays and every abstraction ends in the same state. A result
determined by its inputs has the same history of every lineage as under the agenda; a result
resolved against the context it finds (D1) may take another valid course. All ten examples were
run under 40 random schedules each (400 runs) without a replay failure, and the nine of 0.1.0 also
with workers killed and started again; `docs/distribution.md` gives the details and the limits.

## The contributions of Table 10

| Contribution | Confirmed here by |
|---|---|
| C1 Two interacting relations | `prime-witnesses` (the record resolves 10), `factorization` (certificates checked without search), `payment` (equal payloads, different grounds), `agent` (one proposal, three criteria of its own: ethics, ecology, energy) |
| C2 Inseparable substrate | R2 for every example; `python -m ztes defects`; governed changes in `sqrt2`, `dedekind-cut` and `tsp`; experiment E2: R2 holds even where the history depends on the schedule, which only Principle R excludes |
| C3 Taxonomy of execution outcomes | `sqrt2` (a finite prefix of the unbounded bisection, class 𝔒), `dedekind-cut` (class 𝔓 and its governed repair); experiment E7: what a finite record shows, 𝔗 and 𝔓 from terminal records (𝔓 also in E4) |
| C4 Nondeterminism in the record | `tests/test_workers.py`: the same histories under random schedules; experiment E6: the same verdict in every tested schedule while the abandoned work varies (Corollary 7) |
| C5 Agnosticism | one Z₀ for all ten examples, with no code specific to any of them; `tests/test_config.py`: the same record in memory, on disk, on Redis, in process and over HTTP |
| C6 Reuse and pruning | `tsp` (448 of 720 subproblems), `tsp-bnb` (34 of 1,237 and 14 of 8,660 nodes), the 224 of 227 Pending evaluations of `tour` that stop before the body runs; experiments E3 (each value once, a new root continues the record) and E4 (only demanded arguments: 242 values for f(10⁹)) |

The remaining rows of Table 10 (learned clauses, the adaptive agent, k-SAT) come from
oee-heuristic-agents.

[`docs/glossary.md`](docs/glossary.md) gives the terms of the paper next to those of the output,
in particular Pending in the paper and Not Yet in the output.

## Experiments (not in version 4 of the paper)

[`experiments/README.md`](experiments/README.md) describes seven experiments on control as
interacting relations. Each is run by one command and checked by `tests/test_experiments.py`.

| Experiment | Command | What it prints |
|---|---|---|
| E1 a loop without a loop | `python experiments/run.py e1` | 111 steps, 232 events, the exit on guard(111) = false |
| E2 the end is recorded | `python experiments/run.py e2` | sum 39 in normal form; the control gives 5 under the agenda and by workers a sum that changes with the schedule (for example 16, 17 or 39), and R2 passes for every run |
| E3 the record is the memo and the stack | `python experiments/run.py e3` | A(3, 4): 315 values against 10 307 naive calls; A(3, 5) adds 321; A(3, 7) = 1021 at depth 1023 |
| E4 only what is demanded; a cycle | `python experiments/run.py e4` | f(10⁹) from 242 values; the cycle ends quiescent after 9 events |
| E5 self-similarity | `python experiments/run.py e5` | nine substructures equal to their own records; prefixes that double; exponents 1 and 2 |
| E6 decomposition | `python experiments/run.py e6` | 183 new abstractions; exponents 0.50 and 0.75 against the predicted 1 − 1/k |
| E7 what a finite record shows | `python experiments/run.py e7` | 𝔗 and 𝔓 from terminal records; 𝔒 of `sqrt2-digits` with its specification; `goldbach` undecided: 𝔓 if Goldbach's conjecture holds, 𝔒 otherwise |
