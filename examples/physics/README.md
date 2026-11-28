# Physics on the record

Systems that are not examples of the base paper. They run on the same Z₀ and are written in the
same standard form as the ten examples in [`examples/`](../README.md). Each directory here is one
model, and each model has several systems.

| Model | Systems | What it computes |
|---|---|---|
| [`path-sums`](path-sums/DESIGN.md) | `checkerboard`, `two-slits`, `barrier` | Feynman's sum over paths for a relativistic particle on a lattice, slice by slice, in exact arithmetic |
| [`absorbing-walk`](absorbing-walk/DESIGN.md) | `bright`, `dark`, `dephasing` | a quantum walk on four nodes with an absorbing trap: a dark state, a certificate of unreachability, and a compensation, admitted after it, that adds dephasing; the classes of Theorem 4 |

```bash
python -m ztes run examples/physics/path-sums/checkerboard
python -m ztes run examples/physics/path-sums/two-slits
python -m ztes run examples/physics/path-sums/barrier
python -m pytest -q tests/test_physics.py
python -m ztes run examples/physics/absorbing-walk/bright
python -m ztes run examples/physics/absorbing-walk/dark
python -m ztes run examples/physics/absorbing-walk/dephasing
python -m pytest -q tests/test_absorbing.py
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

The walk is also a bridge between Feynman's path integral and the theory of algorithms: quantum
walks underlie quantum search algorithms and, in another form, models of energy transfer in
photosynthesis. The model design gives the references.

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

## absorbing-walk

A quantum walk on the square 1–2–4–3–1, with node 1 coupled to an absorbing trap. One step is the
Crank–Nicolson form of the continuous-time walk, exactly unitary with entries over 13, followed by
dephasing of strength q and by absorption. The state is a density matrix with exact entries.

Nodes 2 and 3 have the same neighbours, so e₂ − e₃ is a dark state: the step leaves it unchanged,
and it never reaches the trap. The same walk then gives the classes of Theorem 4 for the goals
"absorbed ≥ 1 − 2⁻ᵏ", k = 1, 2, …:
* from a start without a dark part every goal is attained, class 𝔒;
* from a start with one an admitted certificate shows that most goals are unreachable, class 𝔓
  (Proposition 14);
* dephasing, carried by a compensation event that is admissible only after the certificate, makes
  them reachable again (§6.5, Corollary 9).

A classical random walk on the same graph is absorbed with probability 1. Quantum walks with
infinite hitting times, and transport that dephasing assists, are the bridge to the literature;
the model design gives the references, and what this small model does not show.

| System | What it adds | Events | Record |
|---|---|---|---|
| [`bright`](absorbing-walk/bright/DESIGN.md) | start at node 4: G₁ … G₂₁ attained in 40 slices, an unconditional 𝔒 | 52 | 0.06 MB |
| [`dark`](absorbing-walk/dark/DESIGN.md) | start at node 2: half of the walk stays dark; a certificate, checked without search, that absorbed ≤ 1/2 forever: 𝔓 | 53 | 0.06 MB |
| [`dephasing`](absorbing-walk/dephasing/DESIGN.md) | `dark`, then a compensation event, admissible only after the certificate, that carries dephasing q = 1/4: G₂ attained at slice 30 | 76 | 0.14 MB |

The tests (`tests/test_absorbing.py`) are listed in the model design,
[`absorbing-walk/DESIGN.md`](absorbing-walk/DESIGN.md), §7.
