# Local or distributed: an option of the configuration

ZTES executes a system in one process or spread over several, and the difference is one line of
`ztes.yaml`. Nothing in a system changes: the same `system.json`, the same specifications, the
same plan. This page says what the option does, what stays in one place and why, what was tested,
and what it does not claim.

**What this is and is not.** It is a test case: a small demonstration that the execution of the
calculus can be distributed without touching the design of a system. It is one possible
distribution, chosen because it adds little code. It is not the widest distribution the calculus
allows and not a tuned one; §"Limits" lists what a production realization would do differently.

## The two modes

```yaml
execution:
  mode: central     # one agenda and one instance of Z₀ invoke the abstractions in turn
```

```yaml
execution:
  mode: workers     # one worker per abstraction, each with its own instance of Z₀
  local: true       # the workers are threads of this process (false: they run elsewhere)
```

or, for one run, `python -m ztes run examples/factorization --workers`.

| | `central` | `workers` |
|---|---|---|
| who invokes an abstraction | the agenda (`system/agenda.py`) | the abstraction's own worker (`system/workers.py`) |
| instances of Z₀ | one | one per abstraction, and one for the plan |
| who appends to C | that one instance | every worker, by the same conditional insert at position n |
| where ω and τ are evaluated | in process, or in services called by Z₀ (`services`) | inside each worker |
| order of invocations | fixed by the agenda | decided by a race |
| an interrupted run | continued from the record | started again |

Both modes work on every store. With `store.backend: redis` and `execution.local: false` each
worker is a process or container of its own, writing to the one database:

```bash
python -m ztes work examples/factorization targets --config ztes.yaml &
python -m ztes work examples/factorization primes  --config ztes.yaml &
python -m ztes work examples/factorization factor  --config ztes.yaml &
python -m ztes run  examples/factorization         --config ztes.yaml     # the plan; then tells them to stop
```

## Why the order may differ and the result may not

Axiom 0 says what one invocation does on the prefix Cⁿ. It does not say which abstraction is
invoked next. The agenda is one answer; a race between workers is another.

A worker judges on the prefix it has. ω and τ read that prefix only through the **event horizon**
of the abstraction: the lineages its specifications declare. Three consequences carry the whole
mode:

1. **A worker is its own agenda.** After Not Yet or false it waits until an event appears in its
   horizon, or a specification of its own. Events elsewhere cannot change its result and do not
   wake it.
2. **A lost race is usually free.** If another worker takes position n first and its event is
   outside the horizon, the candidate and its judgment are the same on Cⁿ⁺¹ (Lemma 6 of the
   paper), and the worker appends there without computing again (`Z0._stands`). Only an event
   inside the horizon is a reason to judge again. Replay agrees, because on the prefix where the
   event stands it derives the same candidate.
3. **Termination is exact.** A worker that has nothing to add on Cⁿ says so. When all workers say
   it for the same n and n is the length of C, no invocation can extend C. This is the same
   Terminal_r(C) the agenda establishes, and it is not found by waiting for silence. "All"
   includes the workers of abstractions brought in by carried specifications: the coordinator
   adopts them from the same reading of C on which it checks the reports, so a run is never judged
   terminal before an abstraction brought in by its last event has been invoked.

So two runs may give two records. What holds for all of them:

* **every record replays (R2)**: each event is re-derived and re-judged on its own prefix;
* **every abstraction ends in the same state** (closed, or waiting);
* **a result determined by its inputs has the same history** (Theorem K of the paper):
  `dedekind-cut`, `factorization`, `payment`, `sqrt2`, `tsp`, and the tours of `aco`;
* **a result resolved against the context it finds (D1) may take another valid course**:

| Example | What depends on the schedule | What does not |
|---|---|---|
| `prime-witnesses` | which primes `goldbach` admits for an even number (10 = 3 + 7 or 5 + 5): it resolves each even number against the primes recorded when it is invoked | the even numbers answered, the primes, the twins |
| `aco-draw` | how many improvements `best` records (3 to 5): it sees the tours recorded when it is invoked | every draw, every tour, the best length 54 |
| `tsp-bnb` | how many nodes the search expands before a bound is recorded (the record had 70 to 73 events in 40 runs) | the optimal tour, its length 38, the proof of optimality |
| every example | the counts of the profile (invocations, Not Yet, false): they count the schedule | the admitted events they are checked against |

**A rule for the writer of a system.** `prime-witnesses` is the one example in which the schedule
changes an answer and not only the course to it, and it shows why. `goldbach/ontology.v1` proposes
a pair as soon as the primes it sees allow one, so it computes on a horizon that is not yet
complete for its question. `goldbach/ontology.v2`, in the same directory, is ⊥ until every prime
that could take part is recorded; under every schedule it then admits 3 + 7, 3 + 11 and 3 + 17
(`test_waiting_for_the_complete_horizon_makes_the_answer_independent_of_the_schedule`). So:

* an ontology that waits for its complete horizon gives a result determined by its inputs, the
  same under every schedule and after any failure;
* an ontology that answers with what is visible gives a result resolved by the context: valid,
  replayable, and dependent on the schedule.

Both are legitimate designs, and the choice is made in the specification, not in the substrate.

This is not a defect of the mode. It is contextual resolution seen from outside: such an
abstraction has several valid answers, and the record says which one was admitted and on what
prefix. A system states what must hold under every schedule in `"expect": {"any_schedule": …}`
of its `system.json`; without that part, all of `"expect"` holds.

## A worker that fails is a worker that is late

A worker holds no state of its own. What it needs it reads from the record: the prefix, the
active versions, and how many events of its own lineage exist. So a worker that fails is simply
started again:

* the invocation it lost left no event, so nothing in C refers to the prefix it was judged on;
* the new worker judges on the prefix it finds, exactly as a worker that was slow would have;
* if it failed right after its event was appended, the event is in C and the new worker reads it;
* a boundary abstraction with a source lets the source pass the occurrences that its recorded
  events used, and continues with the next one.

A failure therefore changes when an event is appended, and with it possibly the order of C; it
changes nothing that a different schedule could not also change. Every example was run 20 times
with each worker killed at random, before an invocation or right after an append, and started
again (180 runs, 6,270 kills): no replay failure, `expect` held in every run, and the same
lineages kept the history they have under the agenda as in the runs without failures. While a
worker is down the coordinator waits (`execution.timeout`), since termination needs the word of
every worker.

Two things are lost, and neither is in C: the count of the dead worker's invocations that ended
at Not Yet or false (the profile then reports fewer), and, for a source whose occurrence was
refused before the failure, the place of that refusal in its sequence.

## What stays in one place

A minimum of centralization is kept, on purpose.

* **The order of C.** All workers append to one store with one conditional insert, so one place
  decides the order (S1.1). With Redis this is the primary.
* **The plan.** A coordinator records the specifications (phases 1 and 2), the governed changes
  and the KPI, with the workers paused, so that a regime changes as a whole and not one
  specification at a time under running workers.
* **Termination.** The coordinator compares what the workers report.

Workers and coordinator talk through **notes** of the store: small values beside the record
(`control`, `worker|<name>`), overwritten freely. Notes are not events; no judgment reads them and
replay ignores them.

## What was tested

`tests/test_workers.py`, 55 tests, and longer runs of the same checks:

| Configuration | Result |
|---|---|
| all ten examples, workers as threads, on memory, diskcache and Redis (fakeredis, batch 5) | R2 holds, states as under the agenda, `expect` holds |
| all ten examples, each under 40 schedules made by random pauses (400 runs) | no replay failure; the order differed from the agenda's in 296 runs (all 40 of `agent`), and in none for `sqrt2` and `tsp`, whose abstractions strictly alternate; the history of every lineage of `agent` was the agenda's in all 40 |
| `factorization` with three worker processes and a coordinator process on one diskcache record | the 27 events of the agenda, R2 holds, the workers stop when told |
| a race lost to an event outside the horizon | appended one position later, the ontology evaluated once |
| a race lost to an event inside the horizon | judged again, the ontology evaluated twice |
| every example with workers killed at random and started again (4 runs each in the tests, 20 in the longer run) | R2 holds, states and `expect` as without failures; the draws of `aco-draw` are the same draws |
| a worker that starts late | the coordinator waits for it; the record is the usual one |
| no workers running; a worker whose specification fails | the coordinator stops with the reason; the record stays valid |
| the same systems in `central` mode on every store and service option (`tests/test_config.py`) | the same record, event for event |

Not tested here: a real Redis server with replicas, and workers on several machines. Failures
were injected inside one process; a process killed by the operating system behaves the same as
far as the record is concerned, but that was not run.

## Limits

* **Appends do not run in parallel.** C has one order, whatever the number of workers. What runs
  in parallel is the evaluation of ontologies and criteria, so the mode pays off when bodies are
  expensive. In the examples they are cheap: with threads in one process the two modes take about
  the same time for the larger examples (40 to 65 ms), and `central` is several times faster for
  the small ones (3 to 5 ms against 11 to 19 ms), where the workers mostly wait for each other.
* **Workers poll.** An idle worker looks at the record every `execution.poll` seconds. A message
  from the store (publish/subscribe) would wake it sooner and cost less.
* **One primary.** Redis decides the order on one node. Its failover is not consensus; a system
  that must keep every admitted event when nodes fail needs a store whose conditional insert goes
  through consensus (for example etcd). The store interface is small (`get`, `put_if_absent`,
  notes), so this is a new backend, not a new design.
* **One worker per abstraction, started with the run.** Several workers for one abstraction are
  safe for the record (the insert is conditional), but a boundary abstraction with a source would
  need to share the source. A killed worker is started again by whoever runs it (here: by hand,
  or by the test); a worker whose specification fails stops the run. If the coordinator itself
  fails the run is started again, because continuing a plan from the record is implemented for
  the agenda only (`system/resume.py`).
* **A plan that pauses after k admissions** (`"max_admissions"`) is honoured exactly, but which k
  events they are is the schedule's choice.
* **`--trace`** follows the agenda and is not available with workers.
