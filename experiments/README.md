# Experiments: control as interacting relations

Seven small experiments, each answering one question about the calculus of the base paper, *A
Calculus of Execution for Interacting Binary Relations* (version 4,
https://doi.org/10.20944/preprints202608.1545.v4). They show loops, recursion and decomposition
executed as relations that read each other through one record, what this gives without any added
mechanism, the self-similar structure that a recursion leaves in the record, and the four ways an
execution can end. Every experiment is a set of specifications, like the [examples](../examples/README.md);
none adds code to the model or to Z₀. A criterion composed of several normative relations, such
as ethics, ecology and energy, is the example [`agent`](../examples/agent/DESIGN.md).

```bash
python experiments/run.py e1          # one experiment: e1 … e7
python experiments/run.py all         # all of them (about three minutes)
python -m ztes run experiments/e1-loop/while-do     # one system, with its record
```

## What every experiment rests on

**Axiom 0, in one sentence.** An event is appended to the record only if the criterion, a predicate
on the preceding prefix and the completed candidate, is true. Every step of every experiment is one
such admission, and nothing else changes the record.

**The language of bodies has no `while` and no recursion.** A body may use only a bounded `for`,
and a function may not call itself (`ztes/model/language.py`). Every unbounded loop and every
recursion below is therefore an interaction of abstractions over the record, not a construct of the
language.

**The normal form of a criterion.** A criterion reads other lineages only through **positive
atoms**: "an event with this content is in the record", combined with and, or and there exists. Its
own lineage it reads for its position and for uniqueness (an event is recorded once). Every binary
relation is its own characteristic predicate, so the output of any abstraction may stand in a
horizon. What is not a positive atom (an absence, a negation, "all so far", a count, a last value)
enters only as a recorded event, as Principle R (§5.2) requires. A judgment in this form stays true
on every extension of the record, so it does not depend on when it was made. Such judgments are
the persistent propositions of §4.4.8, for which the evaluation on a prefix and the forcing
relation agree.

The examples of the paper do not all use this form: the criterion of `lower` in `sqrt2`, for
instance, reads the last value of `upper`. They rely instead on complete horizons, the hypothesis
of Theorem K: an ontology waits until every event it needs is recorded. The normal form is a
stronger discipline, a sufficient condition and not a necessary one.

**The protocol.** For each system, `run.py`:

1. executes phase 3 under one agenda;
2. replays the record from the empty prefix (R2);
3. executes phase 3 by workers, one per abstraction, each pausing at random before every invocation,
   so that the race is decided differently in every run, and compares the history of every lineage
   with the run under the agenda;
4. measures what the experiment asks and prints it in one table.

Each experiment below has the same parts: the question, the setup, the link to the calculus, what is
measured, the result, and one sentence.

## E1. A loop without a loop

* **Question.** Can a loop run when the language has no `while`?
* **Setup.** `while x ≠ 1 do x := collatz(x)` from x = 27, as three relations
  ([`e1-loop/while-do`](e1-loop/while-do/DESIGN.md)): `state`, the body; `guard`, the predicate
  x ≠ 1, one verdict per state; `exit`, which reads only "guard(k) = false is recorded".
* **Link.** Each step is one admission (Axiom 0). The step is proposed by the ontology and judged by
  the criterion, which recomputes it from the recorded previous state (D2). The loop ends on a
  recorded no, an event with status False, not on the absence of a yes (Definition 6).
* **Result.** 111 steps, largest value 9232, 111 verdicts true and one false, 232 events. R2 replays
  the record; by workers every lineage has the same history in every run.
* **In one sentence.** A loop is a conversation of three relations through the record: the body
  proposes, the guard judges, the exit waits for a recorded no.

## E2. The end is recorded

* **Question.** When may a loop over a stream end?
* **Setup.** The sum of eight items ([`e2-end/iteration`](e2-end/iteration/DESIGN.md)). The end is a
  fact: `more(8) = false`, admissible only because the source admits no ninth item. The control
  ([`e2-end/iteration-absence`](e2-end/iteration-absence/DESIGN.md)) ends when the running sum has
  caught up with the items recorded so far, which reads an absence.
* **Link.** Principle R, Theorem K, and what R2 can and cannot see. The control is an executed
  instance of Proposition 10: read from the interleaving, the outcome depends on it.
* **Result.** In normal form the sum is 39 under the agenda and in every run by workers. The control
  gives 5 under the agenda (it ends after the first item) and by workers a sum that changes with
  the schedule (for example 16, 17 or 39); R2 passes for every run.
* **In one sentence.** Silence is not proof of an end: if the end is not a fact in the record, the
  result depends on the schedule, and replay cannot see it, because every judgment was true on its
  own prefix.

## E3. Recursion: the record is both the memo and the stack

* **Question.** What does a recursion gain with no added mechanism?
* **Setup.** The Ackermann function, which is not primitive recursive, as two relations: `call`
  (who needs whom) and `value` (the function), with `result`
  ([`e3-recursion/ackermann`](e3-recursion/ackermann/DESIGN.md)). First A(3, 4); then a governed
  change makes the root (3, 5), on the same record. And A(3, 7)
  ([`ackermann-deep`](e3-recursion/ackermann-deep/DESIGN.md)).
* **Link.** One event per call (uniqueness in the own lineage) and positive atoms give memoization;
  the record as the continuation removes the stack; the append-only record lets a new root continue
  an old one; the new root enters under R1, and R2 replays across it.
* **Result.**

  | | values recorded | calls of naive recursion | depth of justification |
  |---|---|---|---|
  | A(3, 4) = 125 | 315 | 10 307 | 127 |
  | A(3, 5) = 253 | + 321 on the same record (636 alone) | 42 438 | 255 |
  | A(3, 7) = 1021 | 2558 | | 1023; naive recursion in Python stops with `RecursionError` at its default limit of 1000 |

* **In one sentence.** Nothing is computed twice, depth is not limited by a stack, and a new
  instance continues the old one.

## E4. Only what is demanded; a cycle is recognized

* **Question.** What is computed, and what happens to a circular definition?
* **Setup.** f(n) = f(⌊n/2⌋) + f(⌊n/3⌋), f(0) = 1, for n = 10⁹
  ([`e4-demand/sparse`](e4-demand/sparse/DESIGN.md)); and f(0) = f(1) + 1, f(1) = f(0) + 1
  ([`e4-demand/cycle`](e4-demand/cycle/DESIGN.md)).
* **Link.** The criterion of `value` admits only for a recorded call, so the call relation cuts the
  value relation: pruning by the interaction of two relations. A quiescent record in which the goal
  is not established has status False: class 𝔓 of Theorem 4.
* **Result.** f(10⁹) = 18 639 940 from 242 values, where a table bottom-up needs 10⁹ + 1 entries and
  naive recursion makes 37 279 879 calls. The cycle makes two calls, admits no value, and ends after
  9 events in permanent wait: "its horizon is quiescent".
* **In one sentence.** Only what is demanded is computed, and a closed circle is a quiescence with a
  reason, not a crash.

## E5. The record of a recursion is self-similar

* **Question.** What structure of knowledge does a recursion leave in the record?
* **Setup.** The records of A(m, n) for eight roots ([`e5-self-similarity`](e5-self-similarity/README.md)).
  The justification of a value is the set of recorded values on which its criterion was true.
* **Link.** The positive atoms of a judgment are recorded events, so the justification is a structure
  of the record itself.
* **Result.** (1) In nine of nine pairs, the structure below a value in a larger record equals the
  whole record of that value run alone, on three levels. (2) Each record of A(3, n) is the exact
  beginning of the record of A(3, n + 1) and about twice as long (73, 154, 315, 636); the short reads
  double and the farthest read moves one octave further. (3) The record grows with the depth of
  justification with exponent 1.05, 1.02, 1.01; the unfolded justification with 2.12, 2.06, 2.03.
* **In one sentence.** The record contains itself at smaller scales: a one-dimensional image of a
  self-similar justification of dimension two.

## E6. Decomposition by specializing the criterion

* **Question.** Can a problem divide itself into new abstractions and return the result upward?
* **Setup.** Prove p > 0 on [0, 1] ([`e6-decomposition/split`](e6-decomposition/split/DESIGN.md)). A
  node owns an interval; its criterion is "p > 0 on [LO, HI]". It ends by a certificate (True), a
  witness (False) or the resolution (Not Yet); otherwise its event carries the specifications of two
  children, the same criterion specialized to the two halves. The parent's criterion admits the
  decomposition, τ_root admits the new specifications (R1), and the verdict returns upward through
  positive atoms.
* **Link.** R1 (new abstractions under the same rule), D2, Definition 6, Corollary 7.
* **Prediction.** Nodes split only where the bound cannot yet certify. For contact of order k between
  p and its margin, the number of splits per level grows as ε^−(1 − 1/k).
* **Result.**

  | system | contact | new abstractions | events | splits per level | exponent | predicted |
  |---|---|---|---|---|---|---|
  | `split` | k = 2 | 183 | 280 | 1 2 3 4 6 9 12 16 20 18 | 0.50 | 0.50 |
  | [`split-quartic`](e6-decomposition/split-quartic/DESIGN.md) | k = 4 | 1381 | 2077 | 1 2 4 8 15 27 44 70 112 175 232 | 0.75 | 0.75 |

  When p has a root, the witness x = 5/16 is found at depth 3. With short-circuit and abandonment
  ([`split-witness`](e6-decomposition/split-witness/DESIGN.md), variant 3) the verdict is the same in
  every run, while the abandoned work varies (30 events under the agenda; by workers a number that
  changes from run to run): the nondeterminism is located in the abandoned work, never in the
  verdict (Corollary 7). Waiting for
  both children ([`split-witness-full`](e6-decomposition/split-witness-full/DESIGN.md), variant 1)
  gives the same history of every lineage in every run, at the price of 124 events.
* **In one sentence.** The shape of the decomposition is set by the criterion: the problem divides
  where it cannot yet be certified, by a law that can be predicted in advance.

## E7. What a finite record shows about Theorem 4

* **Question.** What can a finite record say about the class of an execution?
* **Setup.** Four systems, each with a goal recorded as an event. The two that do not stop by
  themselves are observed for a window of 100 admissions.
* **Link.** Theorem 4 and Definition 6. At a prefix, the status of a goal is True when the goal is
  recorded, False when no admissible extension records it, and Not Yet otherwise. A finite record
  shows True directly, and False when it is terminal without the goal. When it is neither, the
  status depends on its extensions: it needs an argument, not a longer window.
* **Result.**

  | system | goal | in the record | terminal | class | shown by |
  |---|---|---|---|---|---|
  | [`while-do`](e1-loop/while-do/DESIGN.md) | the loop has ended | True at C^231 | yes | 𝔗 terminating solution | the record |
  | [`sqrt2-digits`](e7-fates/sqrt2-digits/DESIGN.md) | 10 digits of √2 recorded | True at C^16 | no (100 admissions observed) | 𝔒 correct infinite execution | the record for the goal; the specification for the unbounded stream (`digit` is always defined) |
  | [`cycle`](e4-demand/cycle/DESIGN.md) | f(0) has a value | False | yes | 𝔓 pathological non-progress | the record |
  | [`goldbach`](e7-fates/goldbach/DESIGN.md) | a counterexample to Goldbach | not recorded | no (100 admissions observed) | 𝔓 if Goldbach's conjecture holds, 𝔒 otherwise | nothing in the window |

* **In one sentence.** A terminal record shows 𝔗 or 𝔓, class 𝔒 needs the specification as well,
  and no window shows 𝔚: that class needs a branch that keeps the goal reachable and is never
  taken, as the infinite run of tick events in §6.2 of the paper, so a single order of checks such
  as `goldbach` is never in it.

## Map: claim of the calculus → experiment

| Claim | Experiments |
|---|---|
| Axiom 0; D1 and D2 | all; E1 most directly |
| Normal form of a criterion; Principle R | E2 (control), E6 (abandonment) |
| Theorem K: the same history of every lineage | E1–E4, E6 by workers; E2 and E6 show where it ends |
| R2, and what it cannot see | all; E2 |
| Definition 6: True, False, Not Yet | E1, E6, E7 |
| Theorem 4: what a finite record shows | E4, E7 |
| Corollary 7: the location of nondeterminism | E6 |
| R1: new specifications under the same rule | E3 (governed root), E6 (new abstractions) |
| Optimization with no added mechanism | E3 (memo, no stack, continuation), E4 (pruning by demand, cycles), E6 (abandonment) |
| Self-similar structure | E5 (copies, prefix, dimension 1 against 2), E6 (exponent 1 − 1/k) |

## What the experiments do not claim

* Self-similarity in E5 follows from the recursive definition; what the substrate adds is that the
  record keeps it exactly. The exponents of E5 and E6 are measured on a few instances, with the
  prediction of E6 stated before its measurement for k = 4; they are not proved.
* The control of E2 and variant 3 of E6 depend on the schedule by design; their runs by workers are
  reported, not required to agree.
* E7 reads 𝔗 and 𝔓 only from terminal records. Class 𝔒 of `sqrt2-digits` rests on its
  specification, no window decides `goldbach`, and no experiment exhibits 𝔚.
* Running times are not results: the specifications are written for clarity (the ontology of
  `call` scans the recorded calls), and the larger systems take up to a minute.
