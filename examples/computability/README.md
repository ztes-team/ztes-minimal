# Computability on the record

The four models here and the [seven experiments](../../experiments/README.md) use the same Z₀.
Start with E2 below, or go directly to [reuse](#when-can-one-computation-use-the-work-of-another),
[pruning](#which-search-steps-can-be-skipped), [rule changes](#what-can-change-during-execution)
or [halting](#halting). The [worked examples from the paper](../README.md) have their own reading order.

Run the commands from the repository root with Python 3.12 or later, after `python -m pip install -e ".[test]"`.

## When can a stream be declared complete?

Eight items sum to **39**. In E2 the `more` relation records `more(8) = false` because the source
admits no ninth item. The sum is 39 under the agenda and the tested worker schedules. A control
declares the stream complete as soon as it has consumed everything visible so far. Under the
agenda it stops at **5**. Workers can produce other totals, including 39. Replay (R2) succeeds in
both systems because each admission satisfies its criterion on its own prefix. To see the simpler case of a loop ending on a recorded guard,
run `python experiments/run.py e1`. [E2 stream](../../experiments/e2-end/iteration/DESIGN.md) ·
[E2 control](../../experiments/e2-end/iteration-absence/DESIGN.md) · [E1 loop](../../experiments/e1-loop/while-do/DESIGN.md)

```bash
python experiments/run.py e2
```

## When can one computation use the work of another?

In E3, changing the Ackermann root from A(3,4) to A(3,5) adds **321** values to the existing
record. Computing A(3,5) on its own takes **636** values. E5 then asks which premises justify a
recorded value. In all nine comparisons, the values and their premises match those found when
the smaller problem is run on its own. [E3 recursion](../../experiments/e3-recursion/ackermann/DESIGN.md) ·
[E5 self-similarity](../../experiments/e5-self-similarity/README.md)

The settlement model (§5.4 of the paper) makes reuse an admission decision. Two diagnoses share a funding abstraction.
A matching signature and compatible versions allow the second case to retrieve a published plan
through its declared horizon. The target tests **zero** fresh plans instead of **four**. It still
checks its own amounts and coverage, and refuses payment in the exclusion case.
[Structural memoization](structural-memoization/README.md) · [Measured results](structural-memoization/results/RESULTS.md)

```bash
python experiments/run.py e3
python experiments/run.py e5
python examples/computability/structural-memoization/experiment.py --verify examples/computability/structural-memoization/results/records.json.gz
```

The four systems in the [settlement thread](structural-memoization/thread/DESIGN.md) extend this
example. `regions` checks where a plan is visible, `scaling` and `scaling-pruned` compare the
work of two planners, and `governed` follows revalidation, refunds and closure after a rule change (§9.3).

```bash
python -m ztes run examples/computability/structural-memoization/thread/governed
```

## Which search steps can be skipped?

E4 evaluates a recurrence at 10⁹ from **242** demanded values. Its companion cycle admits two
calls and no value. In the factorization model (§8.7), failed probes on 1121 lead to a residue filter.
After activation the search for 2929 tests **four** centers instead of **six** and certifies the
same factors, 29 × 101. The fresh run constructs the filter on the target. The reuse run reads
the published filter and skips the same two centers.
[E4 demand](../../experiments/e4-demand/sparse/DESIGN.md) · [E4 cycle](../../experiments/e4-demand/cycle/DESIGN.md) ·
[Factorization patterns](factorization-patterns/README.md)

```bash
python experiments/run.py e4
python examples/computability/factorization-patterns/experiment.py --verify examples/computability/factorization-patterns/results/records.json.gz
```

## What can change during execution?

In E6 a subproblem can split when its bounds leave the sign of a polynomial undecided. The split
carries the specifications of two children, each with the parent's criterion specialized to its
own interval. Under the fixed agenda in the witness example, a child finds **x = 5/16** and
the verdict returns to the parent. [E6 decomposition](../../experiments/e6-decomposition/split/DESIGN.md) ·
[Witness and stopping rule](../../experiments/e6-decomposition/split-witness/DESIGN.md)

```bash
python experiments/run.py e6
```

### Governed Goldbach representations

Here a change affects one operand of an existing calculation (§8.3). With both prime addends bounded
by 20, the sum 20 has **four ordered witnesses**. Restricting the second addend to at most 13
removes (3,17) and keeps (17,3). The left transform can be reused, so the second query needs one
fresh forward transform. Replay still validates the original four witnesses at their own prefix.
[Goldbach convolution and controls](goldbach-governed-convolution/README.md)

```bash
python examples/computability/goldbach-governed-convolution/experiment.py --verify examples/computability/goldbach-governed-convolution/results/records.json.gz
```

The three `--verify` commands replay the archived executions. Each model's README also gives the
command to regenerate them. Its experiment driver supplies the observations and the invocation
schedule to the native specifications.

## Halting

**What does a finite record establish about an execution?** E7 illustrates the distinction with
two streams. For √2, the record contains the requested digits and the specification explains why
further digits remain available. The Goldbach stream checks successive even integers for a
counterexample. Its observation window leaves the conjecture open. These goals differ from
counting the witnesses for a bounded sum in the convolution example above.
[E7 digit stream](../../experiments/e7-fates/sqrt2-digits/DESIGN.md) · [E7 Goldbach search](../../experiments/e7-fates/goldbach/DESIGN.md)

```bash
python experiments/run.py e7
python -m ztes run examples/computability/halting/finish-fair
python -m pytest -q tests/test_halting.py
```

The classical halting problem remains undecidable (§4.5). The six systems below illustrate the evidence
available for a particular goal under a fixed regime. A halting configuration witnesses termination.
A checked repetition certificate can establish non-halting for a particular machine. The
`finish-unfair` and `finish-unreachable` windows have the same execution payloads, yet the
specifications give different answers about whether `finish` remains reachable. R2 rechecks
each recorded admission on its prefix. In the table, 𝔗 denotes a terminating solution, 𝔒 a
correct infinite execution, 𝔓 pathological non-progress and 𝔚 perpetual Not Yet.
[Halting model](halting/DESIGN.md) · [Glossary](../../docs/glossary.md)

| System | Goal | What the record and specifications establish | Recorded events |
|---|---|---|---:|
| [Machines](halting/machines/DESIGN.md) | A machine reaches a halting configuration | Three Busy Beaver champions halt (𝔗). Two machines have checked non-halting certificates (𝔓 for the halting goal). All five reach the separate goal of recording a verdict. | 183 |
| [Collatz](halting/collatz/DESIGN.md) | Each positive integer reaches 1 | For the first 1,000 integers, reusing earlier results takes 5,379 steps against 59,542 counted separately. The unbounded regime is 𝔒 if the conjecture holds and 𝔓 otherwise. | 1,009 |
| [Antihydra](halting/antihydra/DESIGN.md) | The recurrence reaches b = −1 | The window covers 1,000 iterations of a six-state machine's recurrence. The class is 𝔗 if the goal is ever reached and 𝔓 otherwise, never 𝔚; which of the two is not known. | 1,012 |
| [Fair finish](halting/finish-fair/DESIGN.md) | Record `finish` | A scheduler drawing from the recorded seed reaches the goal after six ticks (𝔗). | 26 |
| [Unfair finish](halting/finish-unfair/DESIGN.md) | Record `finish` | The source for this run always gives zero. The goal stays reachable at every prefix and is never selected (𝔚 for the unbounded run). The window covers 40 admissions. | 50 |
| [Unreachable finish](halting/finish-unreachable/DESIGN.md) | Record `finish` | The active policy can only propose ticks (𝔓). The execution payloads match the unfair window. | 50 |

The machine certificates cover exact repetitions and repetitions shifted into blank tape. In either
case, the same segment repeats without reaching a halting configuration (Proposition 14). The
physics model of §6.5 also gives an example of 𝔒, a certificate of 𝔓 and a governed change that restores
reachability. [Absorbing walk](../physics/absorbing-walk/DESIGN.md)

## Tests (`tests/test_halting.py`)

<details>
<summary>What each halting test checks</summary>

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
| `test_the_fair_scheduler_is_the_seeded_source_one_decision_at_a_time` | `draw(6, k)` equals the k-th occurrence of the source of `sources.py`; no decision is proposed while another waits; the record is that of the agenda under every schedule |
| `test_unfair_and_unreachable_have_the_same_payloads_and_different_classes` | the same execution payloads, decisions and ticks; at every prefix of the window a decision for finish is admissible in `finish-unfair`, and finish follows it after an even number of ticks, while in `finish-unreachable` the decision is computed and is always tick. The window shows the pattern; the claim for every prefix rests on the specifications |

</details>

The [record tests](../../tests/test_records.py) check the archived lengths and digests. Other tests
exercise [both replay modes](../../tests/test_replay_modes.py), [store configurations](../../tests/test_config.py)
and [workers under different schedules](../../tests/test_workers.py).
