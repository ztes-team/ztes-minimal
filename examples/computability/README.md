# Computability on the record

Systems that are not examples of the base paper. They run on the same Z₀ and are written in the
same standard form as the ten examples in [`examples/`](../README.md). Each directory here is one
model, and each model has several systems.

| Model | Systems | What it shows |
|---|---|---|
| [`halting`](halting/DESIGN.md) | `machines`, `collatz`, `antihydra`, `finish-fair`, `finish-unfair`, `finish-unreachable` | the modalities of halting, all four classes of Theorem 4, with the evidence for every verdict |

```bash
python -m ztes run examples/computability/halting/machines
python -m ztes run examples/computability/halting/collatz
python -m ztes run examples/computability/halting/antihydra
python -m ztes run examples/computability/halting/finish-fair
python -m ztes run examples/computability/halting/finish-unfair
python -m ztes run examples/computability/halting/finish-unreachable
python -m pytest -q tests/test_halting.py
```

## halting

The systems illustrate how Theorem 4 classifies outcomes. A class belongs to a maximal execution
of a fixed regime, relative to a family of persistent goals; a record is a finite prefix of such an
execution, and for an unbounded regime a window of it. Taken together, the rows show executions in
each of the four classes. Two regimes can produce the same execution payloads while differing on
whether `finish` remains reachable, and each machine verdict is supported by a halting
configuration or by a checked certificate.

The halting problem stays undecidable (§4.5). What the record adds:
* the evidence for every verdict: a halting configuration, or a certificate;
* a criterion that checks a certificate instead of searching for it (D2, Proposition 14);
* a replay (R2) that re-derives every verdict from its prefix.

The model design is in [`halting/DESIGN.md`](halting/DESIGN.md).

| System | What it adds | Goal | Class of the maximal execution | Events |
|---|---|---|---|---|
| [`machines`](halting/machines/DESIGN.md) | three Busy Beaver champions halt; two machines never halt, each with a checked certificate | a halting configuration of M is recorded | champions 𝔗; certified machines 𝔓. For the goal "a verdict is recorded" the same task terminates, 𝔗 | 183 |
| [`collatz`](halting/collatz/DESIGN.md) | each number reaches 1 by an induction over the record (5,379 steps recorded instead of 59,542 for n ≤ 1,000) | n reaches 1, for every n ≥ 1 | 𝔒 if the conjecture holds, otherwise 𝔓; the specification has no bound, and the record is a window of 1,000 admissions | 1,009 |
| [`antihydra`](halting/antihydra/DESIGN.md) | the recurrence of a six-state machine whose halting no one has decided | b = −1 is recorded | 𝔗 or 𝔓, unknown, never 𝔚; the window is 1,000 iterations of the recurrence, not steps of the machine | 1,012 |
| [`finish-fair`](halting/finish-fair/DESIGN.md) | tick/finish of §6.2 with a recorded, fair scheduler | finish is recorded | 𝔗; the record is the whole execution | 26 |
| [`finish-unfair`](halting/finish-unfair/DESIGN.md) | the same, with a scheduler that never chooses finish: reachable at every prefix | the same | 𝔚 for the unbounded run; the source that always gives 0 is the environment of this run, not part of the regime; a window of 40 admissions | 50 |
| [`finish-unreachable`](halting/finish-unreachable/DESIGN.md) | a deterministic scheduler that never proposes finish | the same | 𝔓; the same execution payloads as `finish-unfair`, a different specification of `policy` | 50 |

A certificate (i, j) shows that configuration j repeats configuration i, exactly or shifted into
blank tape, with no halting configuration between them. By induction on the number of repetitions
the computation from j repeats the steps i … j forever, so no future step halts (Proposition 14). An unconditional 𝔒 is in E7 (`sqrt2-digits`); machine 5 would give one, for the goals "the record
contains a configuration in which cell k holds a 1", if `run` did not stop at its certificate.

## Tests (`tests/test_halting.py`)

| Test | Checks |
|---|---|
| `test_halting_example_is_well_formed_and_meets_its_expected_end` | `check` passes; the run meets `"expect"` |
| `test_halting_example_replays_in_process_and_over_http` | R2; the same record with every abstraction as an HTTP service |
| `test_the_champions_halt_where_an_independent_simulator_says` | 6, 21 and 107 steps; 4, 5 and 13 ones; every recorded configuration equals that of an independent simulator |
| `test_the_certified_machines_do_not_halt_and_a_wrong_certificate_is_refused` | 10⁵ steps without halting, as the certificate proves for every step; another pair, or a claim that the machine halts, is refused (D2) |
| `test_collatz_every_number_of_the_window_reaches_1_and_none_is_checked_twice` | an independent check for every n ≤ 1,000; 5,379 recorded steps; 59,542 to 1 |
| `test_collatz_a_piece_must_stop_at_the_first_value_below_its_number` | the piece of 27 has 96 steps; a longer or a shorter one is refused |
| `test_collatz_short_pieces_add_up_and_a_piece_has_at_most_L_steps` | with L = 2 the indicator adds every piece of a number (8 steps to 1 for n ≤ 3), and a piece longer than L is refused |
| `test_antihydra_follows_the_rules_and_records_no_verdict` | every iteration equals the recurrence of bbchallenge; no goal; b never below 0 |
| `test_the_fair_scheduler_finishes_after_an_even_number_of_ticks` | decisions 0, 1, 0, 0, 1, 0, 0, 0, 1; finish after 6 ticks |
| `test_unfair_and_unreachable_have_the_same_payloads_and_different_classes` | the same execution payloads, decisions and ticks; at every prefix of the window a decision for finish is admissible in `finish-unfair`, and finish follows it after an even number of ticks, while in `finish-unreachable` the decision is computed and is always tick. The window shows the pattern; the claim for every prefix rests on the specifications |

The general tests of the examples also cover these systems:
* the pinned records (`test_records.py`);
* both replay modes (`test_replay_modes.py`);
* every store and configuration (`test_config.py`);
* workers on every store and under random schedules (`test_workers.py`).
