# Physics on the record

Systems that are not examples of the base paper. They run on the same Z₀ and are written in the
same standard form as the ten examples in [`examples/`](../README.md). Each directory here is one
model, and each model has several systems.

| Model | Systems | What it computes |
|---|---|---|
| [`path-sums`](path-sums/DESIGN.md) | `checkerboard`, `two-slits`, `barrier` | Feynman's sum over paths for a relativistic particle on a lattice, slice by slice, in exact arithmetic |

```bash
python -m ztes run examples/physics/path-sums/checkerboard
python -m ztes run examples/physics/path-sums/two-slits
python -m ztes run examples/physics/path-sums/barrier
python -m pytest -q tests/test_physics.py
```

`run` shows a long value by its beginning and its length. `python -m ztes run … --record DIR`
keeps the record, and `python -m ztes explain DIR N` shows event N whole.

## path-sums

The model computes the standard exact method for a discretized path integral: the sum over all
paths is computed one time slice at a time, by the distributive law. It adds no computational power
(§4.5 of the paper). What the record adds:
* the record is the memo table;
* a contribution is pruned only where an argument shows it cannot matter;
* a governed change of the experiment reuses what stays valid;
* conservation of probability is part of the admission criterion;
* R2 replays every value bit for bit, because every value is exact (integers and rationals).

Time in these systems is the step of the walk, a value in the record; ZTES itself has no time
([`path-sums/DESIGN.md`](path-sums/DESIGN.md), §1).

The model design, and what this does not claim, is in [`path-sums/DESIGN.md`](path-sums/DESIGN.md).

| System | What it adds | Events | Record |
|---|---|---|---|
| [`checkerboard`](path-sums/checkerboard/DESIGN.md) | the free particle against all 2¹⁶ paths and against a closed form; one amplitude at T = 32 on two light cones; reuse across questions | 50 | 0.07 MB |
| [`two-slits`](path-sums/two-slits/DESIGN.md) | interference, and a which-path detector as a governed change; the slices before the screen serve both experiments | 89 | 0.21 MB |
| [`barrier`](path-sums/barrier/DESIGN.md) | tunnelling through a mass barrier, the transmitted probability exactly, for five widths | 237 | 1.4 MB |

## Tests (`tests/test_physics.py`)

| Test | Checks |
|---|---|
| `test_physics_example_is_well_formed_and_meets_its_expected_end` | `check` passes; the run meets `"expect"` |
| `test_physics_example_replays_in_process_and_over_http` | R2; the same record with every abstraction as an HTTP service |
| `test_long_values_are_shown_shortened` | `run` shows a value of thousands of characters by its beginning |
| `test_checkerboard_equals_the_sum_over_all_paths` | at T = 16 the recorded slice equals the sum over all 65,536 paths and the closed form, exactly |
| `test_checkerboard_one_amplitude_on_two_cones_needs_no_more` | the amplitude at (0, 32) equals the closed form and the walk on the whole cone; probability is conserved with what was cut |
| `test_checkerboard_reuses_and_never_computes_a_slice_twice` | 33 slices, none twice; question 2 starts at t = 17 |
| `test_a_wrong_digit_or_a_coin_that_is_not_unitary_is_refused` | D2: one changed amplitude is refused; a coin with a² + b² ≠ 1 is refused at its first step |
| `test_monte_carlo_over_paths_meets_the_sign_problem` | 20,000 sampled paths: relative error 2 % at T = 4, more than 100 times the value at T = 32 |
| `test_two_slits_patterns_differ_by_the_interference_term_only` | the coherent amplitude is the sum of the two parts; equal totals; P₁ − P₂ = 2·Re ψ⁽¹⁾ψ⁽²⁾* at every site |
| `test_two_slits_reuse_the_slices_before_the_screen` | 41 + 31 slices, none twice; what the screen stops is recorded |
| `test_barrier_transmission_falls_with_the_width_then_meets_the_over_barrier_part` | the five exact transmitted probabilities, falling by more than 4 per site, then slowly |
| `test_barrier_cut_changes_no_transmitted_value` | the cut on the left changes no transmitted probability (walk without a cut) |

The general tests of the examples also cover these systems:
* the pinned records (`test_records.py`);
* both replay modes (`test_replay_modes.py`);
* every store and configuration (`test_config.py`);
* workers on every store and under random schedules (`test_workers.py`).
