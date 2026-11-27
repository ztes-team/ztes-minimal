# Tests

`python -m pytest -q` runs every test, and `python -m pytest --collect-only -q` lists them. This
page lists the main tests of the model, the substrate and the tooling and what each shows. The
tests of the examples are listed in
[`examples/README.md`](../examples/README.md#tests-of-the-examples), and
[`REPRODUCING.md`](../REPRODUCING.md) names the test behind each result of the paper.
Section, theorem and table numbers refer to version 4 of the base paper.

| Test | What it shows |
|---|---|
| `test_plan_runs_and_replays` | the √2 plan gives the expected bounds and R2 holds |
| `test_phase2_requires_phase1` | an ontology cannot be recorded before its criterion |
| `test_tampering_is_detected` | a value changed outside Z₀ is found at that event, and the next hash link breaks (Theorem C′ in miniature) |
| `test_concurrent_substrates_do_not_fork` | two instances of Z₀ judge the same prefix; one append succeeds, the other is judged again |
| `test_redis_backend` | the same system on Redis |
| `test_the_same_record_under_every_configuration` | every example gives the same events in memory, on disk, on Redis (batch 1 and 7), with services on a replica, and over HTTP |
| `test_every_example_by_workers_on_every_store`, `test_every_example_under_random_schedules` | phase 3 by one worker per abstraction: every record replays, every abstraction ends the same way, `expect` holds under any schedule |
| `test_a_lost_race_outside_the_horizon_keeps_the_judgment` | Lemma 6 in Z₀: a judgment stands while its horizon stands |
| `test_workers_as_separate_processes` | three worker processes and a coordinator on one record |
| `test_a_service_waits_for_its_replica` | a lagging replica delays the run and does not change the record |
| `test_an_append_no_replica_confirmed_stops_the_run_and_the_run_continues` | replica confirmation; the run continues from the record |
| `test_command_line` | `run` with a kept record, then `verify`, and `verify --judgments` |
| `test_malformed_system_is_refused` | a file whose version does not match its name is refused at load |
| `test_sqrt2_termination_states` | √2 ends terminal: `lower` closed, `upper` in permanent wait |
| `test_generic_context_and_external_wait` | `count`, `all` + `where`, record payloads, a wait on an external lineage |
| `test_tau_root_checks_the_api` | unknown `select`, missing criterion default, unknown type are refused |
| `test_types_are_strict` | values of the wrong type are rejected |
| `test_check_accepts_the_shipped_systems` | `check` passes for √2 and for the test system |
| `test_check_finds_problems` | an undeclared name, a missing file, a criterion refused by τ_root |
| `test_comprehensions_see_bindings` | regression: generator expressions in a body see the bindings |
| `test_http_services_carry_json_candidates` | regression: over HTTP, integer and record candidates keep their type |
| `test_authoring_format_is_expanded` | identity from the path, named types and bindings, `$self`, list context, used constants only; the expanded form runs and replays |
| `test_select_one_and_where_with_earlier_bindings` | `select: one` and a `where` that uses an earlier binding; more than one match is an error |
| `test_errors_name_the_specification_and_expression` | a failing body is reported with its specification and expression; `a / b` gives a clear message |
| `test_expect_reports_differences` | `expect` detects wrong event counts, states and values |
| `test_a_failing_specification_stops_the_run_with_its_location` | `run` stops with exit code 2 and names the failing expression |
| `test_function_body_rules` | a function body may not use while, import, `_` attributes, recursion, or undeclared names |
| `test_tau_root_checks_function_bodies` | τ_root refuses a function body with an undeclared parameter or a while loop |
| `test_new_creates_a_valid_skeleton` | `new` gives a system that passes `check` and runs to termination |
| `test_trace_shows_bindings_and_steps` | `--trace` shows bindings, intermediate values and judgments |
| `test_explain_shows_the_ground_of_an_event` | `explain` re-derives an event from its prefix |
| `test_separate_microservice_processes` | two `serve` processes and Z₀ in a third share one record |
| `test_index_gives_the_same_answers_as_a_plain_list` | the record index answers exactly as a scan of the list |
| `test_large_record_is_linear` | 2,000 admissions run and replay within seconds |
| `test_python_api_from_dict_and_save` | a system built in code runs, meets `expect`, and is saved in the standard form |
| `test_library_rules_and_subset` | helper functions: only the used ones (and what they call) are copied; no recursion, no call to a later helper |
| `test_derived_values_are_computed_once_and_immutable` | a derived value is computed once and cannot be altered by a body |
| `test_map_binding_is_incremental_read_only_and_prefix_exact` | a map is read-only, exact for every prefix, and refuses duplicate keys |
| `test_tau_root_refuses_a_map_that_reads_another_binding` | a map may not depend on other bindings, so it can be kept between invocations |
| `test_model_does_not_import_the_substrate` | no module of `ztes.model` imports `ztes.substrate` or `ztes.system` |
| `test_validation_gives_located_reasons` | a malformed specification is described by what is wrong and where |
| `test_refusal_names_the_reason` | τ_root says why it refuses: a version gap, a missing criterion |
| `test_a_service_reads_its_prefix_without_the_store` | a service evaluating on Cⁿ is served from the cache |
| `test_notes_are_for_the_reader_only` | `"note"` fields are removed before a specification is recorded |
| `test_kpi_profile_records_what_the_record_does_not_keep` | the profile of √2: invocations, admissions, ⊥, τ false; A agrees with C |
| `test_profile_criterion_refuses_an_inconsistent_observation` | a profile whose A differs from C, with I ≠ A + U + F, or with decreasing counts is refused |
| `test_tampering_with_a_profile_is_detected` | R2 re-judges a boundary occurrence: a changed U is found |
| `test_tsp_kpi_measures_reuse_on_demand` | the KPI of `tsp`: 448 of 720 subproblems, 272 saved; 230 wake-ups of `tour` |
| `test_run_writes_metrics_as_json` | `run --metrics FILE` writes the indicators as JSON |
| `test_the_record_is_the_pinned_one`, `test_every_example_is_pinned` | every example gives, under the agenda, the record pinned in `tests/test_records.py` (number of events and a digest of the whole record): an optimization must leave every record identical |
| `test_the_cached_filter_gives_what_the_uncached_one_gives` and the other tests of `tests/test_filter_cache.py` | a filter that reads only `x` is decided once per event and kept in the index; it gives what the uncached filter gives for every select, window and prefix, and the same errors; a filter that reads a constant or a binding is not cached |
| `test_a_sound_record_passes_both_modes`, `test_the_faster_mode_finds_every_defect_but_the_hidden_draw` | the replay that re-judges recorded candidates without re-deriving them passes every sound example and finds seven of the eight defects of Table 5, all at the same event but the overwritten tour (one event later, by the hash link); it misses the hidden draw |
| `test_the_values_are_those_of_the_plain_binding_frozen` and the other tests of `tests/test_frozen.py` | a frozen binding gives the values of the plain binding, frozen, for every prefix, filter and window; they are shared and immutable; τ_root refuses a frozen binding whose filter reads another binding; a system that reads its history frozen runs and replays to the same values |
| `test_the_compiled_decoder_gives_what_the_old_decode_gave` and the other tests of `tests/test_decoders.py` | the decoder compiled once per type gives what the recursive decode gave, value for value and error for error, on random types and values |
| `test_a_carried_ontology_is_active_from_its_event_and_replays` and the other tests of `tests/test_carried.py` | a specification carried by a candidate is active from its event and replays in both modes; a criterion and its ontology carried together bring in a new abstraction, executed by the agenda and by workers; τ_root judges carried specifications in order (version gaps, an ontology without its criterion, two carried fields), and a refused candidate leaves C unchanged; an abstraction that does not read the proposer is evaluated again; a carrying candidate is judged again after a lost race; an interrupted run continues to the same record; the same histories under random schedules; an altered carried specification fails replay at its event; a constant may name the specification files a proposer carries |
| `test_criterion_v2_accepts_exactly_the_next_prime` and the other tests of `tests/test_prime_criterion.py` | the optional next-prime criterion of `prime-witnesses` and `factorization` admits exactly the next prime at every prefix, where criterion v1 also admits 4 and 5 on an empty lineage; admissions on each side of the change keep their evidence; a sparse lineage [5] continues with 7; the optional plan adds one specification event and keeps the domain payloads; both replay modes across the change |
| `test_failed_map_extension_matches_fresh_index` (`tests/test_map_recovery.py`) | a map binding whose batch fails (a value that cannot be computed, a key that occurs twice in the recorded prefix or in the new batch) fails again in the same way when read again, and a shorter prefix reads as a fresh evaluation |

These tests concern the model and the substrate and are grouped by package (`tests/test_model.py`,
`test_substrate.py`, `test_system.py`, `test_cli.py`, and `test_records.py`, `test_filter_cache.py`,
`test_decoders.py`, `test_frozen.py`, `test_replay_modes.py` for the optimizations, `test_carried.py` for
specifications carried in execution, `test_prime_criterion.py` for the optional next-prime criterion, `test_map_recovery.py` for a map
binding after a failed batch); they use `examples/sqrt2` and
`tests/systems/counter`, a small system written in the same standard form. The examples have their
own tests (`tests/test_examples.py`), described in [`examples/README.md`](../examples/README.md).

## Experiments (`tests/test_experiments.py`)

| Test | What it shows |
|---|---|
| `test_experiment_system_meets_its_expected_end_and_replays`, `…_e6_e7_…` | every system of the experiments passes `check`, meets its `expect` and replays (R2) |
| `test_normal_form_gives_the_same_history_of_every_lineage` | Theorem K, executed: E1–E4 by workers under random schedules give the history of every lineage of the agenda |
| `test_e1_the_loop_ends_on_a_recorded_no` | the loop ends on guard(111) = false, an admitted event |
| `test_e2_an_end_read_from_an_absence_depends_on_the_schedule_and_replays_anyway` | Principle R: the control admits on an absence; R2 passes, and the schedule changes the result |
| `test_e3_values_are_recorded_once_and_a_later_root_continues_the_record` | 315 values for A(3, 4), 321 more for A(3, 5) on the same record; the unfolded justification and its depth |
| `test_e3_depth_without_a_stack` | A(3, 7) at depth 1023 in the record, where naive recursion raises `RecursionError` |
| `test_e4_only_demanded_arguments_and_a_quiescent_cycle` | 242 values for f(10⁹); the cycle ends with two calls and every abstraction in permanent wait |
| `test_e5_the_record_of_a_recursion_contains_itself` | substructures equal to the records run alone; one record the prefix of the next |
| `test_e6_decomposition_returns_upward_and_its_front_has_the_predicted_exponent` | 183 nodes brought in during the run, exponent 0.50; the same history by workers, one per node |
| `test_e6_contact_of_order_four_gives_the_exponent_three_quarters` | the prediction 1 − 1/k for k = 4 (about a minute) |
| `test_e6_short_circuit_fixes_the_verdict_and_waiting_fixes_every_lineage` | variant 3: the same verdict in every schedule tested; variant 1: the same history of every lineage in five runs. It is also the regression test of the coordinator of workers, which once judged a run terminal before abstractions brought in by the last event had been invoked |
| `test_e7_what_a_finite_record_shows` | 𝔗 and 𝔓 read from terminal records; the goal of `sqrt2-digits` recorded in a run that goes on; `goldbach` decided by no window |
