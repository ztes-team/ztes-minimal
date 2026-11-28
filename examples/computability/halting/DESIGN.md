# Halting on the record: the model (step 0)

*Not an example of the paper. Six systems on the same Z₀: [`machines`](machines/DESIGN.md),
[`collatz`](collatz/DESIGN.md), [`antihydra`](antihydra/DESIGN.md), [`finish-fair`](finish-fair/DESIGN.md),
[`finish-unfair`](finish-unfair/DESIGN.md), [`finish-unreachable`](finish-unreachable/DESIGN.md). Base
paper: Lemma 7 (§6.1), Definition 6, Theorem 4 (§6.2), Proposition 14, §4.4.8, §5.2. Tags: [C]
epistemic, [ω] ontological, [τ] eschatological (see [`examples/README.md`](../../README.md)).*

**What this model adds.** Halting in its modalities, executed on the record. One model covers:
* machines that halt, a finite witness;
* machines that never halt, with a certificate the criterion checks without search;
* a recorded induction that establishes infinitely many goals one by one;
* a machine at the frontier of what is known, on which no finite record decides anything;
* a goal that stays reachable at every prefix and is never taken.

The systems illustrate how Theorem 4 classifies outcomes. A class belongs to a maximal execution
of a fixed regime, relative to a family of persistent goals; a record is a finite prefix of such an
execution, and for an unbounded regime a window of it. Taken together, the rows show executions in
each of the four classes. Two regimes can produce the same execution payloads while differing on
whether `finish` remains reachable, and each machine verdict is supported by a halting
configuration or by a checked certificate. The class depends on the regime and on the
family of goals, not on the record alone.

**What it does not claim.** The halting problem stays undecidable (§4.5). The certificates are sound
but incomplete: a machine that never halts may have no certificate of the kinds used here. The
frontier machine stays open. The record adds:
* the evidence for every verdict;
* a criterion that checks a certificate instead of searching;
* a replay (R2) that re-derives every verdict from its prefix.

## 1. Background

A deterministic Turing machine M with two symbols starts on a blank tape. By Lemma 7, M halts
exactly when the goal H_M, a recorded halting configuration, is reachable in the regime r(M) of its
step schedule. In OEE terms:
* **A halting machine** establishes H_M at a finite prefix, the affirmative reading of §4.4.8: an
  open property, once it holds, is affirmed at a finite prefix.
* **A machine that never halts** has status False for H_M at every prefix. It is one branch, so it
  is in class 𝔓, never in 𝔚. A False status can require an unreachability argument
  (Proposition 14). A certificate is such an argument with a finite, effectively checkable
  representation.
* **No finite record** shows that a machine without a certificate never halts.

The Busy Beaver program studies exactly these modalities. S(5) = 47,176,870 was proved in Coq in
2024 by the bbchallenge collaboration, which decided each of 181,385,789 machines with five states:
the halting ones by running them, the others by checkable non-halting certificates ("deciders").
For six states the frontier is open. The machine Antihydra halts if and only if a Collatz-like
process, the map n ↦ ⌊3n/2⌋ from n = 8, ever reaches more odd values than twice the number of even
ones. Whether it does is unknown.

References: The bbchallenge Collaboration, *Determination of the fifth Busy Beaver value*,
arXiv:2509.12337; https://bbchallenge.org/antihydra.

## 2. The systems

| System | Goal | Class of the maximal execution | What the record shows |
|---|---|---|---|
| `machines` | a halting configuration of M is recorded; five machines, each a governed question | 𝔗 for the three champions; 𝔓 for the other two. For the goal "a verdict is recorded" the same task terminates, 𝔗 | the halting configuration, or a certificate checked by the criterion |
| `collatz` | n reaches 1, for every n ≥ 1, a countable family of goals | 𝔒 if the Collatz conjecture holds, otherwise 𝔓; the specification has no bound | a window of 1,000 admissions: a recorded induction, each n checked only until it falls below n |
| `antihydra` | b = −1 is recorded | 𝔗 or 𝔓, never 𝔚; unknown which | a window of 1,000 iterations of the recurrence (not steps of the machine), no verdict |
| `finish-fair` | finish is recorded; a fair boundary scheduler | 𝔗 | the whole execution: finish after an even number of ticks |
| `finish-unfair` | the same; the scheduler never chooses finish | 𝔚, for the unbounded run with this source | a window: ticks only; finish reachable at every prefix |
| `finish-unreachable` | the same; a deterministic scheduler that never chooses finish | 𝔓 | a window: the same execution payloads as `finish-unfair`, a different specification of `policy` |

E7 (`experiments/e7-fates`) asks what a finite record shows about Theorem 4. This model executes the
modalities with their evidence, and E7's `goldbach` and `sqrt2-digits` stay its companions.

## 3. `machines`: halting and certified non-halting

**Machines** (standard bbchallenge notation; Z is the halting state):

| Machine | Transitions | Behaviour, checked by simulation |
|---|---|---|
| BB(2) champion | `1RB1LB_1LA1RZ` | halts after 6 steps, 4 ones |
| BB(3) champion | `1RB1RZ_1LB0RC_1LC1LA` | halts after 21 steps, 5 ones |
| BB(4) champion | `1RB1LB_1LA0LC_1RZ1LD_1RD0RA` | halts after 107 steps, 13 ones |
| a cycler | `1LB0RB_1LC0LC_0RA1RZ` | the configuration at step 6 equals that at step 0: never halts (checked to 10⁵ steps) |
| a translated cycler | `1RB0LB_1RC1RA_1LB1RZ` | steps 0 and 6: the same state, the head 2 cells further right, blank to its right, and never left of its position at step 0 in between: never halts (checked to 2·10⁵ steps) |

The two machines that never halt have a halting transition (C1 → 1RZ) that they never take.

**Abstractions.**
* **`run`** records one step of the machine at a time: `{"m": 3, "k": 17, "state": "D", "head": -1,
  "lo": -3, "tape": [1, 1, 0, 1, 0]}`. Its criterion checks one transition against the recorded
  configuration before it (D2). It is ⊥ at a halting configuration, once a verdict is recorded, or
  at the step bound K.
* **`verdict`** records the answer for the machine: `{"m": 3, "halts": true, "steps": 107, "ones": 13}`,
  or `{"m": 4, "halts": false, "certificate": ["cycle", 0, 6]}`. The ontology searches the recorded
  configurations for a certificate. The criterion checks the given pair (i, j) only, without search:
  * **cycle:** configuration j equals configuration i;
  * **translated:** at step i every cell from the head to the right is blank; between i and j the
    head never moves left of its position at i; at j the state is the same, the head is further
    right, and every cell from it to the right is blank.

  Each is an inductive invariant in the sense of Proposition 14. A certificate (i, j) shows that configuration j repeats configuration i, exactly or shifted into blank tape, with no halting configuration between them. By induction on the number of repetitions the computation from j repeats the steps i … j forever, so no future step halts (Proposition 14).
* **Governed questions.** Each machine is a new version of `run` and `verdict` (M = 1 … 5). An
  evolutive change ends a regime, so each machine is classified in its own regime.

**The class depends on the family of goals.** For the translated cycler and the goal H_M the run is
in 𝔓. For the countable family "cell k holds a 1" (k = 0, 1, 2, …) the same run is in 𝔒, since each
cell is written at a finite step and stays 1. The record is the same; Theorem 4 is relative to 𝒢.

**Expected end:** 151 configurations and 5 verdicts, 183 events with the KPI step.

## 4. `collatz`: infinitely many goals, established by a recorded induction

T(n) = n/2 for even n, and 3n + 1 for odd n. The goal 𝒰_n is that n reaches 1.

* **`segment`** takes the smallest n whose goal is not established. It is read from the last
  recorded piece, so it is never searched for. It records the trajectory from n until the first
  value below n: `{"n": 27, "path": [27, 82, 41, …, 23], "below": true}`.
* **The criterion** checks every step of the path and that it ends below n. Every m < n is already
  established, so n reaches 1 by induction over the record. The record is the memo table: the rest
  of the trajectory is never computed again.
* **A bounded body** (the language rule). A trajectory longer than the bound L would be recorded in
  pieces, each continuing the last. A divergent n would therefore produce pieces forever. Its goal
  would never be established, and the run would be in 𝔓.

**Expected end** for n = 1 … 1,000 (1,009 events with the KPI step):
* 5,379 steps are recorded, where following every trajectory to 1 would take 59,542 steps (91 %
  saved);
* the longest piece is that of n = 703, which takes 132 steps to fall below 703.

No window decides the conjecture: as with `goldbach` in E7, each goal is established at a finite
prefix, and the class of the unbounded run is known only if the conjecture is.

## 5. `antihydra`: the frontier

The rules of Antihydra (bbchallenge):
* start with a = 8, b = 0;
* each step: if a is even, b increases by 2, otherwise b decreases by 1; then a becomes a + ⌊a/2⌋;
* the machine halts when b = −1.

* **`rule`** records one step, `{"k": 12, "a": 1021, "b": 12}`, and the criterion checks it.
* **`halt`** records the goal if b = −1 is ever recorded.
* **The window** is 1,000 iterations of the recurrence (1,012 events with the KPI step). There b = 497 (499 even values,
  501 odd), b never falls below 0 after the start, and a has 177 digits.

The run is one branch: it is in 𝔗 if b ever reaches −1, and in 𝔓 otherwise, never in 𝔚. No finite
record decides which.

The equivalence of these rules with the six-state machine `1RB1RA_0LC1LE_1LD1LC_1LA0LB_1LF1RE_---0RA`
is a lemma of bbchallenge, cited and not checked here. The system executes the rules, not the
machine.

## 6. `finish-fair`, `finish-unfair`, `finish-unreachable`: 𝔚 against 𝔓

This is the tick/finish example of §6.2, with the scheduler made explicit, as Principle R asks of
order. A `policy` lineage records which abstraction acts next: "tick" or "finish".
* **`tick`** records a tick when the latest decision is "tick".
* **`finish`** records finish when the latest decision is "finish" and the number of ticks is even.
  A decision for finish at an odd count is refused, and the policy decides again.

| System | `policy` | Every prefix | The unbounded run |
|---|---|---|---|
| `finish-fair` | a boundary abstraction (§5.2), its occurrences drawn from a seeded source | finish is reachable, so the status is Not Yet until it is taken | 𝔗: finish is taken after an even number of ticks |
| `finish-unfair` | the same boundary abstraction; the source always gives "tick" | finish is reachable: a different occurrence is admissible at every decision, so the status is Not Yet | 𝔚 |
| `finish-unreachable` | an ordinary abstraction whose ontology always proposes "tick" | finish is unreachable, and the status is False; certificate: every admissible decision is "tick" | 𝔓 |

The records of `finish-unfair` and `finish-unreachable` carry the same execution payloads, decisions
and ticks, and their classes differ; the recorded specification of `policy` differs. The status of a prefix is a property of the regime, which here is the specifications of
`policy`, not of the events recorded so far. The two unbounded runs are windows: the record of 40
admissions is paused, not terminal, as in E7.

**The decisions do not depend on the schedule.** A source gives one occurrence per invocation of
`policy`, also when the occurrence is refused. The criterion of `policy` therefore admits every
well-formed decision while finish is not recorded, and `tick` and `finish` act on the recorded
decisions in order. The decisions are the occurrences of the source in order, under the agenda and
under workers. With seed 6 they are 0, 1, 0, 0, 1, 0, 0, 0, 1: two decisions for finish come after
an odd number of ticks and are void, and finish is taken after 6 ticks (26 events). Under workers
`policy` may record more decisions before finish is recorded; the finish is the same.

## 7. Relation to other approaches

The distinctions of Theorem 4 have counterparts elsewhere; what differs is what they are computed
over.
* **Temporal logics and model checkers** (LTL, CTL, TLA+, Spin). Over a model of a system, a
  branching-time logic separates a goal that stays reachable (EF goal) from one that is unreachable
  (AG ¬goal). A strong fairness condition on finish separates `finish-fair` from `finish-unfair`,
  where finish is enabled infinitely often and never taken. The classes of Theorem 4 belong to this
  tradition (Alpern and Schneider). Here the tree is that of a regime whose specifications are
  events of the same append-only record. It changes by governed admission (R1), and the status of a
  recorded prefix is re-derived by replay (R2). In a model checker the specification is an input to
  the tool, and a change of rules has to be encoded in the state of the model.
* **Event sourcing and ledgers.** They keep an append-only log and often validate each entry
  deterministically, close to the criterion (D2). The log records what was admitted, usually not
  the specification that proposed it (D1). From the log and its rules alone it therefore cannot tell
  apart three reasons why an entry is absent: a realization is pending; a candidate was admissible
  but the scheduler chose another (`finish-unfair`); or no realization can propose it
  (`finish-unreachable`).
* **Proof assistants** (Coq, Lean). They check proofs and certificates step by step, and re-checking
  a proof is a replay of its steps by the kernel; S(5) = 47,176,870 was established that way, with
  certified deciders. A proof assistant can establish once that a kind of certificate is sound. The
  record here admits instances of such certificates inside an execution, under a recorded criterion
  that governance can change, and replays each admission from its own prefix. The two are
  complementary.

## 8. Design decisions

* **One event per machine step, per rule step, and per Collatz piece.** Each criterion checks one
  step or one piece against the record.
* **D2: the ontology searches, the criterion checks.** `verdict` searches for a certificate; its
  criterion checks a given pair. `segment` follows a trajectory; its criterion checks a given path.
* **Certificates only of a finite, checkable kind (Proposition 14).** Two kinds for machines, the
  recorded induction for Collatz. Nothing is inferred from absence: a missing verdict is not a
  verdict.
* **Exact integers.** Tapes, counters and the 177-digit a of Antihydra are integers in C.
* **No time.** A step k, a decision or a piece is a value in the record (see the physics model,
  `examples/physics/path-sums/DESIGN.md` §1).

## 9. Runs

| System | Events | Record | Run | Replay (R2) |
|---|---|---|---|---|
| `machines` | 183 | 0.16 MB | 0.2 s | 0.1 s |
| `collatz` | 1,009 | 0.39 MB | 0.1 s | 0.1 s |
| `antihydra` | 1,012 | 0.44 MB | 0.1 s | 0.05 s |
| `finish-fair` | 26 | 0.01 MB | < 0.1 s | < 0.1 s |
| `finish-unfair`, `finish-unreachable` | 50 each | 0.02 MB | < 0.1 s | < 0.1 s |

## 10. Tests (`tests/test_halting.py`)

The tests are listed in [`../README.md`](../README.md#tests-teststest_haltingpy). The general tests
of the examples cover these systems too: pinned records, both replay modes, every store and
configuration, and workers on every store and under random schedules.

## 11. Not in this step

* **The BB(5) champion.** It runs 47,176,870 steps, so it would take macro steps: one event per 10⁶
  steps, 48 events, and a criterion that recomputes each macro step. A run and its replay would take
  a minute or more.
* **A cycle certificate for Collatz.** None can occur below 1,000.

* Further certificate kinds of bbchallenge (bouncers, finite automata reduction), where Proposition
  14 needs a symbolic invariant.
* The six-state Antihydra machine itself, step by step, with its rules checked against it.
* Langton's ant: its trajectory is unbounded (Bunimovich and Troubetzkoy), and the highway appears
  after about 10,000 steps from a blank grid. It is a candidate for a goal affirmed at a finite
  prefix with a certificate of persistence.
