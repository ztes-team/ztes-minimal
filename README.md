# ZTES: a minimal Zero Tier Execution Substrate for the OEE calculus

A minimal executable substrate for the calculus in *A Calculus of Execution for Systems of
Interacting Binary Relations: Contextual Resolution, Separated Admission, and an Inseparable
Execution Substrate* (Škarić, Ivanović, M. Radenković, Prokhorov, Labus, B. Radenković) [2].
Preprint: DOI to be added.

This repository is one possible implementation of the ZTES execution model [3], which is
independent of infrastructure and design method; here it serves to demonstrate the calculus.

A problem is decomposed into binary relations. Each relation is lifted into an executable
specification, an **abstraction**. The **zero-tier execution substrate Z₀** executes the
abstractions: it applies Axiom 0, records every admitted step in one shared record, and is the only
writer to that record, from which every step can be verified later. The substrate is small on
purpose: it shows the ideas of the paper, not every case.

New here? [`docs/tour.md`](docs/tour.md) follows one invocation from start to finish, maps the paper
to the code, and walks through the examples.

## Theory in brief

**Binary relations as the starting point.** A relation R ⊆ X × Y says which pairs belong together.
It does not say how a pair is produced, on what grounds it was accepted, or how that acceptance can
be checked later. The calculus adds exactly this, without changing what R is (§1, §4.3).

**Scope.** Set theory and number theory can be formalized in the calculus of binary relations [1],
and higher-arity relations reduce to binary incidence relations (§2.1). Most problems of mathematics
and of the formally grounded sciences can therefore be stated as interacting binary relations and
executed by this model, within S1. Execution adds verifiable steps and finite witnesses, not proofs
of universal statements (§8.3).

**Lifting.** A relation is lifted into an abstraction with three components:

| Component | Name in the paper | Role |
|---|---|---|
| the shared record C | epistemic axis | append-only history of admitted events; the context of every step |
| the ontology Sω | ontological axis, ω | proposes a candidate y from the context; partial: may be undefined (⊥) |
| the criterion Sτ | eschatological axis, τ | judges a completed candidate; total and Boolean |

**One rule of execution: Axiom 0, applied by Z₀.** Z₀ is the fixed, domain-independent procedure that
applies Axiom 0 over C: the zeroth tier, presupposed rather than admitted, below every abstraction
(§3.4.1). For a prefix Cⁿ: if Sω(Cⁿ) is undefined, nothing happens
(**Not Yet**). Otherwise the candidate ω is judged by Sτ(Cⁿ, ω), and only on `true` is the event
⟨coordinate, ω⟩ appended, giving Cⁿ⁺¹. Iterating this rule is **eschatological induction** (§3.4,
§4.1.3).

**Two ideas.**
* **D1, contextual resolution.** A relation may allow many y for one x. The substrate never chooses
  among them: the record resolves the ontology to at most one candidate (§3.2.2).
* **D2, separated admission.** The criterion is an independent object, specified and versioned
  separately from the ontology, and judged on the same prefix (§3.1.3, Proposition 15).

**The architecture S1 and what it guarantees.** One append-only shared order, a deterministic
criterion, immutable specification versions activated only through the record, retained evidence,
and a certified record (§3.3). Together these give

* **R1**: governance follows the same rule as execution: a new specification version is itself an
  admitted event and is active only from then on;
* **R2**: every admitted event can be re-derived from its prefix and the recorded specifications.

The conditions are inseparable: dropping any one of them loses R1 or R2 (Theorems B, C, C′, D,
§4.2.1). S1 together with Z₀ is the execution substrate: S1 is its architecture and Z₀ the procedure
that executes over it.

**Termination.** A system is terminal when no abstraction can extend the record (§4.6.5). Each
abstraction then is either **closed** (it has a candidate, but the criterion refuses it) or in
**permanent wait** (Not Yet, and nothing it reads can still change).

## Method: from a problem to an execution

| Step | What you do | What the substrate does | Where |
|---|---|---|---|
| **0. Decompose** | Write the problem as binary relations R ⊆ X × Y. | – | `DESIGN.md` |
| **0. Lift** | For each relation write two short JSON specifications: a criterion (what may be admitted) and an ontology (how a candidate is obtained from the record). X is read from the record through declared bindings; Y is the payload. Shared types, constants and bindings are declared once. | expands them into complete specifications; `check`: well-formedness, declared names, admissibility under τ_root | `abstractions/` |
| **0. Plan** | List the abstractions, the plan, and the expected end in `system.json`. | – | `system.json` |
| **1. Criteria** | – | records every criterion as an event, admitted under τ_root; no evaluation | `Z0.admit_criterion` |
| **2. Ontologies** | – | binds every ontology to its admitted criterion and records it; no evaluation | `Z0.admit_ontology` |
| **3. Execute** | – | applies Axiom 0 to the abstractions on an agenda until the system is terminal | `Z0.execute`, `System.run` |
| **Change** | Write a new version and add a `govern` step. | records it as an event; the changed abstraction runs again | plan step `govern` |
| **Verify** | – | replays the whole record from C alone (R2) and compares the end with `expect` | `substrate/replay.py`, `check_expect` |

This README describes the substrate only. Two separate documents complete it:

* [`docs/writing-a-system.md`](docs/writing-a-system.md): how to write a system, with the full
  reference of the JSON files (part of the substrate documentation);
* [`examples/README.md`](examples/README.md): the examples from the paper, each in its own directory,
  described separately from the substrate.

## Quick start

```bash
pip install -r requirements.txt        # or: pip install -e ".[test]"  (Python 3.12 or later)
python -m ztes new    my-system --abstractions a,b      # the skeleton of a new system
python -m ztes check  examples/sqrt2                    # static check, nothing is executed
python -m ztes design examples/sqrt2 [--full]           # the abstractions; --full: expanded specifications
python -m ztes run    examples/sqrt2                    # execute, show the record, verify (R2), compare with expect
python -m ztes run    examples/sqrt2 --trace            # also show bindings and intermediate values
python -m ztes run    examples/sqrt2 --metrics [FILE]   # the latest execution indicators (KPI); FILE: also as JSON
python -m ztes run    examples/sqrt2 --record DIR       # keep the record, e.g. to archive it
python -m ztes verify DIR                               # replay an existing record
python -m ztes explain DIR 5                            # why event 5 is in the record
python -m ztes run    examples/sqrt2 --http             # each abstraction as an HTTP microservice (threads)
python -m ztes run    examples/sqrt2 --redis URL        # distributed record (Redis)
python -m pytest -q
```

End of `python -m ztes run examples/sqrt2`:

```
   terminal: no abstraction can extend C in this regime
     lower        closed: ω = 181/128, τ false
     upper        permanent wait (Not Yet): its horizon is quiescent

   n  kind    abstraction  value
   0  genesis
   1  spec    lower        criterion v1   addr …
   2  spec    upper        criterion v1   addr …
   3  spec    lower        ontology v1   addr …
   4  spec    upper        ontology v1   addr …
   5  exec    upper        3/2   ≈ 1.500000
   6  exec    lower        5/4   ≈ 1.250000
   7  spec    lower        criterion v2   addr …
   8  spec    upper        criterion v2   addr …
   9  exec    lower        11/8   ≈ 1.375000
  10  exec    upper        23/16   ≈ 1.437500
  11  exec    lower        45/32   ≈ 1.406250
  12  exec    upper        91/64   ≈ 1.421875

R2  replay of 13 events: OK
```

## How the substrate works

### Components: the model and the substrate

The package keeps the **model**, what a specification is and how it is evaluated, apart from the
**substrate** Z₀ that records and executes it. Dependencies go one way: `system` → `substrate` →
`model`. The model does not import the substrate (a test checks this) and never writes C; the
substrate contains no domain content.

Every module starts with a header naming the parts of the paper it implements, and docstrings and
comments use one set of tags:

| Tag | Part of the model | |
|---|---|---|
| `[C]` | epistemic axis: the record, what is read from it (κ(C)), how it is written | |
| `[ω]` | ontological axis: Sω, realization, ⊥ (Not Yet) | D1 |
| `[τ]` | eschatological axis: Sτ, judgment, exactly one Boolean | D2 |
| `[Z₀]` | the zero-tier execution substrate: Axiom 0, τ_root, the only writer to C | §3.4.1 |
| `[A0]` | one application of Axiom 0: an invocation, steps 3a, 3b, 3c | |
| `[S1.k]`, `[R1]`, `[R2]` | the substrate conditions and what they guarantee | §3.3, §4.2 |

The same tags mark the specifications of the examples (`"note"` fields, comments in function
bodies), so that every part of a system says which axis it belongs to.

| Package | Module | Role | Paper |
|---|---|---|---|
| **model**: the OEE model | `epistemic.py` [C] | κ(C): bindings over C, maps, constants, derived values; the horizon a specification declares | §9.1.1, S1.4, Def. 10 |
| | `ontological.py` [ω] | Sω: realization, ω or ⊥ | §3.4.1, D1 |
| | `eschatological.py` [τ] | Sτ: judgment, exactly one Boolean | §3.4.1, D2 |
| | `view.py` [C] | the record as the model reads it: a prefix Cⁿ as a view, and its index | S1.1, §9.1 |
| | `language.py` | the language of bodies: expressions, functions, libraries (`lib.py`); determinism | §3.4.4, S1.2 |
| | `types.py` [C] | codecs between JSON payloads and computed values | §3.2.5 |
| | `validation.py` | well-formedness of a specification as an API, with located reasons | §3.4.4 |
| | `explain.py` | the same evaluation step by step (`--trace`, `explain`) | – |
| | `errors.py` | ⊥ (`Undefined`) and defects of specifications (`SpecError`) | §3.4.1 |
| **substrate**: Z₀ and C | `store.py` [C] | the medium of C: append-only; the only write is one atomic conditional insert | S1.1, §9.1 |
| | `events.py` [C] | events ⟨coordinate, payload⟩ and Rec; hash link to the previous event | §3.2.5, S1.2, S1.4, S1.5 |
| | `lookups.py` [C] | admitted and active versions, event horizons | S1.3, Definition 10 |
| | `governance.py` [Z₀] | τ_root: the API (model.validation) and the lineage in C; gives the reason of a refusal; the specifications a candidate carries | §3.4.1, §4.2.7, R1 |
| | `z0.py` [Z₀] | **Z₀**: Axiom 0; phases 1, 2, 3; the only writer to C | §3.4.1, §3.4.3 |
| | `replay.py` [R2] | R2 replay; each check is named by the S1 condition it protects | §4.2.6, Theorem C′ |
| | `service.py` [ω][τ] | one stateless microservice per abstraction: Z₀ asks it for steps 3a and 3b | §3.4.4, §9.1.1 |
| **system**: tooling | `authoring.py` | step 0: short specification files and shared declarations, expanded into complete specifications | – |
| | `system.py` | load a system, run its plan, start its services | – |
| | `agenda.py` [Z₀] | phase 3: the agenda, termination, the final state of each abstraction | §4.6.5, §6.2 |
| | `checks.py` | the static check of a system, with the same rules as τ_root | – |
| | `kpi.py` | execution indicators as abstractions above Z₀: `profile` (boundary) and the system's `kpi` | §5.2, §6.3 |
| | `report.py` | the record as text, `explain`, `expect`, the R2 report | – |
| | `scaffold.py` | `new`: a valid starting system with DESIGN.md | – |
| | `__main__.py` | `new`, `check`, `design`, `run`, `verify`, `explain`, `serve` | – |

(`service.py` sits at the top of the package, as the boundary between Z₀ and the model.)

### Phase 3: one invocation of Axiom 0

```
3a  ω := Sω(Cⁿ)                    ⊥ → Not Yet: τ is not called, nothing is appended   (D1)
3b  b := Sτ(Cⁿ, ω)                 false → nothing is appended                        (D2)
3c  put_if_absent(n, Rec(Cⁿ, ω))   only if b is true
```

Phases 1 and 2 only record specifications. Evaluation happens only in phase 3. Not Yet is not a
value of either function: it is the decision of Z₀ not to append when ω is undefined in Cⁿ.

### Specifications carried by a candidate

A specification enters C in one of two ways, both judged by τ_root: the plan records it from a file
(phases 1 and 2, the step `govern`), or a candidate carries it in phase 3. An ontology whose record
type has one field of type `{"list": "specification"}` carries, in that field, the specifications
it proposes. In one invocation:

```
3a  ω := Sω(Cⁿ); every ontology ω carries is bound to the criterion active at its place (as in phase 2)
3b  b := Sτ(Cⁿ, ω)                 the criterion of the proposer judges the whole candidate
    τ_root, in order               each carried specification on Cⁿ and the ones before it; one refused → false
3c  put_if_absent(n, Rec(Cⁿ, ω))   one execution event; its coordinate lists what it carries
```

Every carried specification is an admitted version from that event on (S1.3), and replay checks
it as a specification event. Z₀ knows no kinds of abstraction: who may change what is a question
for the criterion of the proposer, which may read a policy recorded in C. An abstraction whose
specifications are carried goes back on the agenda, and one the system did not have is adopted
(`System.adopt`), by workers with a worker of its own. Whether a change takes effect at the same
position under every schedule is a property of the system: the proposer decides at every point
where a decision is due, and the abstractions it may change wait for that decision. The design is
in [`docs/specifications-in-execution.md`](docs/specifications-in-execution.md); how to write such
a system, in [`docs/writing-a-system.md`](docs/writing-a-system.md).

### Atomic append

The key of an event is its position n. Z₀ takes Cⁿ, obtains ω and the judgment on that
prefix, and writes with `put_if_absent(n, event)`: diskcache `add` under the key `C|n`, or Redis
`SET {record}|n … NX`. If
another instance of Z₀ has already written position n, the insert fails. If the event that took the
position is outside the event horizon of the abstraction, the candidate and its judgment are the same
on Cⁿ⁺¹ (Lemma 6) and the insert is repeated there; otherwise the invocation is judged again
on Cⁿ⁺¹. Z₀ does not read back what it has appended: an admitted event costs one request to the
store. An invocation that appends nothing (Not Yet, false) is reported only after one request has
confirmed that position n is still free, that is, that Cⁿ was the latest prefix. The event at position n is therefore always one whose candidate and judgment hold on exactly Cⁿ. A pre-incremented
counter would not give this guarantee, because it reserves a position before the judgment. Each
event also carries the hash of its predecessor, so the record certifies itself (S1.5).

### What the substrate does when something goes wrong

| Situation | Behaviour |
|---|---|
| the process stops after any event | the append is atomic, so C is a valid prefix. Running the same plan on the same record continues it: the schedule is walked again against the record (`system/resume.py`), nothing is rewritten, and the result is the record an uninterrupted run would give, the KPI profile included |
| the store holds a record of another system | the first event that differs is reported (`DifferentRecord`); nothing is appended |
| a stored event was changed | every event is checked against the hash of its predecessor when it is first read; execution stops (`CorruptRecord`). `verify` reads without that check, because its task is to say where and why the record fails |
| an abstraction service does not answer | steps 3a and 3b write nothing, so the call is repeated (`services.retries`, each within `services.timeout`); then the invocation ends with `ServiceUnavailable` and nothing is appended |
| a service reads a replica that does not hold Cⁿ yet | the service waits (`read.wait`) and never answers on a shorter prefix; replica lag costs time and cannot change a judgment. If the replica stays behind: `ServiceUnavailable`, nothing appended |
| Redis does not give the durability asked for | the store does not open (`NotDurable`) |
| an append is not confirmed by the required replicas | the run stops (`NotDurable`); the event is on the primary, and the same command continues from the record |
| a specification fails while it is evaluated | `SpecError` with the location of the expression; the run stops, the record stays valid |
| two instances of Z₀ judge on the same prefix | one conditional insert succeeds; the other appends one position later if its horizon is untouched, and judges again if not |

Addresses of specifications and the links between events are full SHA-256 hashes; the listing of a
record shows their first sixteen characters.

### The agenda and termination

Phase 3 is driven by an agenda, as in a three-phase simulation:

1. At the start every abstraction is on the agenda.
2. Z₀ takes one abstraction and applies Axiom 0.
   * **admitted:** the abstraction and every abstraction whose horizon contains it go back on the
     agenda;
   * **Not Yet or false:** the abstraction leaves the agenda and waits. Not Yet has two grounds:
     the horizon is incomplete (a required event is not in Cⁿ; the body is not evaluated), or the
     body, computed on a complete horizon, yields no candidate. false means that a candidate exists and τ refuses it on this prefix. Its result depends only on
     the events in its horizon and on its active specifications, so it can change only when one of
     those lineages gains an event or when a governed change gives it a new specification.
3. **The agenda is empty.** No abstraction generates events, and no abstraction waits for an event
   that can still occur in its horizon: Terminal_r(C) holds. Because every body is a terminating
   expression over declared inputs, this is established exactly, not estimated by waiting.

A governed change starts a new regime (§4.6.5): the changed abstraction goes back on the agenda and
execution continues. Lineages outside the system (external abstractions) deliver no events yet, so
their readers stay in permanent wait. A criterion that never closes would run forever; the
substrate stops at an admission limit and reports that the system is not terminal.

### Deployment as separate microservices

`run --http` starts the services as threads of one process, for demonstration. In a deployment each
abstraction runs as its own process, reading the shared record, and Z₀ calls them by URL:

```bash
python -m ztes serve examples/sqrt2 lower --port 8701 --redis redis://host:6379/0
python -m ztes serve examples/sqrt2 upper --port 8702 --redis redis://host:6379/0
echo '{"lower": "http://host:8701", "upper": "http://host:8702"}' > services.json
python -m ztes run   examples/sqrt2 --redis redis://host:6379/0 --services services.json
```

The services never write to C; only Z₀ does, through the atomic conditional insert. A
specification that fails inside a service is reported to Z₀ with its location, as in-process.
`--record DIR` instead of `--redis` shares a local record between processes on one machine.
The same deployment is written once in `ztes.yaml` (next section): each service then reads the
replica nearest to it, and only Z₀ talks to the primary.

### Configuration: `ztes.yaml`

`system.json` says what is executed; `ztes.yaml` says on what. The file in this repository states
the defaults, and every option is in it:

```yaml
store:
  backend: redis                      # memory | disk | redis
  url: ${ZTES_PRIMARY}                # the primary, the only place Z₀ appends
  record: sqrt2                       # several records may share one database
  durability: always                  # always | everysec | none: checked when the store opens
  replicas: 1                         # replicas that must confirm every append (WAIT)
  batch: 256                          # events fetched by one read (MGET)
read:
  url: ${ZTES_REPLICA}                # the replica next to this service
  wait: 5.0                           # seconds a service waits until the replica holds Cⁿ
services:
  timeout: 10.0
  retries: 2
  urls: {lower: "http://lower:8701", upper: "http://upper:8702"}
```

`./ztes.yaml` is read if present, `--config FILE` names another, a value `${NAME}` comes from the
environment, and `--record`, `--redis`, `--http`, `--services` override the file. An unknown option
is an error, not a silent default.

**The configuration cannot change the record.** The same system gives the same events in memory,
on disk, on Redis with any batch size, with services in process, over HTTP, or reading a replica
(`tests/test_config.py` runs every example under these). What can change the record
(`admission_limit`, the seed of a source) is therefore in `system.json`, not here.

One option changes the order of events and nothing else: `execution.mode`.

### Local or distributed execution

```yaml
execution:
  mode: workers     # one worker per abstraction, each with its own instance of Z₀ (default: central)
```

or `python -m ztes run examples/factorization --workers`. In `central` mode one agenda and one
instance of Z₀ invoke the abstractions in turn. In `workers` mode every abstraction is a worker
that reads the record, applies Axiom 0 and appends to the one shared record itself; with Redis
and `execution.local: false` each worker is a process or container of its own
(`python -m ztes work SYSTEM ABSTRACTION`). The system is not touched: the same specifications
and the same plan are executed.

The order of invocations is then decided by a race, which Axiom 0 allows. Every record so
obtained replays under R2 and every abstraction ends in the same state. A result determined by
its inputs has the same history as under the agenda; a result resolved against the context it
finds (D1) may take another valid course. All nine examples were run under 360 random schedules
without a replay failure. A worker that fails is started again and continues from the record:
it holds no state of its own, so a failure is a delay (180 runs with 6,270 injected failures).

This is a demonstration that the execution can be distributed as an option of the configuration.
It is one possible distribution, kept small, and not the widest or the fastest one.
[`docs/distribution.md`](docs/distribution.md) explains what stays in one place, what was
tested, and the limits.

Three properties make the distributed form simple. There is one writer path: Z₀ appends to the
primary with a conditional insert, so the order of C is decided in one place (S1.1). Everything
else only reads prefixes Cⁿ, which never change, so any replica can serve any service, and each
store object keeps what it has read; that is the whole cache, and it is never invalidated. And a
service names the prefix it needs by its length n: a replica that is behind makes it wait, so
replica lag affects speed and never a judgment. Not Yet is a different thing: it is a fact of Cⁿ
(ω is undefined there), and it is the same on every replica that holds Cⁿ.

### Execution indicators (KPI): abstractions above the substrate

KPI are not part of the calculus; they belong to the design of an execution. They are ordinary
abstractions, admitted by Z₀ under Axiom 0, that are invoked only when an indicator is needed: a plan
step `{"kpi": true}` (every example has one, at the end), or `System.measure(z0)` at any moment.
Admitted events are immutable, so nothing has to be computed before it is asked for. No primitive is added
(`system/kpi.py`):

* **`profile`**, generated for every system, is a boundary abstraction (§5.2: `"boundary": true`).
  Its candidate is the count of outcomes the agenda has observed for each abstraction: I
  invocations, A admitted, U ⊥ (Not Yet), F τ false, and H, the part of U
  decided by the horizon alone: a required event was not in Cⁿ and nothing was computed. U − H and
  F are then the invocations that computed without producing an event. U and F leave no event in
  C, so this is how they enter it. The criterion checks what C confirms (A equals the events of
  that abstraction, I = A + U + F, 0 ≤ H ≤ U, counts never decrease); the payload is retained as evidence and R2 re-judges it.
* **`kpi`**, optional and specific to a problem (`"kpi": "kpi"` in `system.json`), is an ordinary
  abstraction: its bindings read the latest profile and any domain lineage, so it can compute any
  indicator of that execution. An abstraction that reads its lineage (a heuristic agent) sees the
  indicators and is evaluated again after they are admitted; a new indicator is a governed change.

Counting outcomes is the agenda's bookkeeping, one counter per invocation; Z₀ and the model are
unchanged. `run --metrics [FILE]` adds a KPI step at the end if the plan has none and prints the
latest indicators (FILE: also as JSON). For `examples/tsp`:

```
   abstraction         I      A      U      H     F      α  state
   dp                450    448      2      0     0   1.00  wait
   tour              230      3    227    224     0   0.01  wait
   kpi: {"profile": 1, "questions": 3, "subproblems": 448, "needed": 720, "saved": 272, "tour_invocations": 230, "tour_not_yet": 227}
```

`saved` is what the record spared three independent Held–Karp runs; `tour` is woken after every
subproblem and is ⊥ 227 times, a property of its horizon visible only in the indicators; 224 of
them cost nothing, because its ontology declares the subproblems it requires (`"requires"`) and
the body is not evaluated before they exist. Cost: one
counter per invocation (not measurable in the TSP timings), and a KPI step of 0.2–0.3 ms (3 ms the
first time, when the KPI specifications are recorded); the record grows by two events per step.

### Performance

A single writer makes about 1.2 to 1.5 requests to the store per event: one append per admitted
event and one confirmation per invocation that appends nothing. Reads from Redis come in batches.
Each store object reads every event once: C is append-only, so events already read are kept with an
index (by lineage, by specification address, by version) and only new events are fetched. A prefix
Cⁿ is a view of the first n events, not a copy, and a service evaluating on the prefix that Z₀ has
just read does not touch the store at all. A binding decodes only what it needs (`count` and
`exists` decode nothing, `last` decodes one value). A `map` binding is kept in the index and
extended with each new event, so a body that looks up recorded values by key does not rebuild a
table from the whole lineage. What a specification needs independently of C (its namespace,
constants and derived values) is prepared once; expressions, function bodies and libraries are
compiled once; event horizons are computed once per pair of active versions.

Measured on this machine: 20,000 events of two interacting abstractions run in 0.8 s in memory and
3.4 s with diskcache, and replay in 0.4 s. The exact TSP of `examples/tsp`, run for a single
instance:

| Cities | Subproblems | Run | Per subproblem | Replay (R2) |
|---|---|---|---|---|
| 8 | 448 | 0.05 s | 0.1 ms | 0.02 s |
| 10 | 2,304 | 0.22 s | 0.1 ms | 0.08 s |
| 11 | 5,120 | 0.46 s | 0.1 ms | 0.18 s |

The cost of one invocation does not grow with the record: the ontology of `dp` reads the next
subproblem from the record (`ORDER[done]`) instead of searching for it, and every lookup goes
through the index. A phase-3 step stops at `admission_limit` (default 10,000; settable in
`system.json`), a guard against criteria that never close.

### Python API

A system can also be built in code and stored in the standard form:

```python
from ztes.substrate.replay import verify
from ztes.substrate.store import DiskStore, read
from ztes.system.system import System

system = System.from_dict({
    "system": "squares", "abstractions": ["sq"], "constants": {"N": 5},
    "bindings": {"k": {"from": "$self", "select": "count"}},
    "specifications": {
        "sq/criterion.v1": {"inputs": {"context": ["k"], "candidate": {"name": "w", "type": "integer"}},
                            "body": {"result": "k < N and w == k * k"}},
        "sq/ontology.v1":  {"inputs": {"context": ["k"]}, "returns": "integer",
                            "body": "def omega(k):\n    return k * k\n"},
    },
})
store = DiskStore("record")
system.run(store)
assert verify(read(store)) == []
system.save("examples/squares", design="# squares …")     # the same system as a directory
```

## Tests

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
own tests (`tests/test_examples.py`), described in [`examples/README.md`](examples/README.md).

## Repository layout

```
ztes/                     independent of any system
  model/                  the OEE model: epistemic [C], ontological [ω], eschatological [τ],
                          view, language, types, validation, explain, errors
  substrate/              Z₀ and C: store, events, lookups, governance (τ_root), z0, replay (R2)
  system/                 tooling: authoring, system, agenda, resume, checks, report, scaffold, kpi,
                          sources (occurrences for boundary abstractions), workers (phase 3 by one
                          worker per abstraction)
  defects.py              the eight defective mechanisms of Table 5
  service.py              an abstraction as a microservice (the boundary between Z₀ and the model)
  config.py               ztes.yaml: store, durability, replica, services
  __main__.py             the command line
docs/tour.md              a guided walk: one invocation, paper ↔ code, the examples, the defects
docs/writing-a-system.md  how to write a system; reference of the JSON files
docs/distribution.md      local or distributed execution as an option of the configuration
examples/README.md        the examples, described separately
examples/<name>/          one directory per example: system.json, DESIGN.md, abstractions/, lib.py
ztes.yaml                 the configuration, with its defaults
tests/                    test_model, test_substrate, test_system, test_cli, test_examples, test_config,
                          test_workers
```

## The eight conditions, broken one at a time

`python -m ztes defects` runs the ant colony of `examples/aco` on a sound mechanism and then on
eight defective ones (`ztes/defects.py`), one for each essential condition of S1 (Theorem C,
Table 5; the deviations of Theorem D). Each defect is something an ordinary implementation of the
method would do, and each is found by the ordinary replay, which reads only the record:

| | Condition | The deviation | Replay stops with | Lost |
|---|---|---|---|---|
| 1 | append-only (S1.1) | evaporation overwrites a stored tour | the realization no longer matches the record | R2 |
| 2 | shared order (S1.1) | a writer that has not seen a governing event admits a tour | criterion version not active | R1 |
| 3 | recorded inputs (S1.2) | the random generator is kept outside the record | the realization is ⊥, the record has a tour | R2 |
| 4 | immutable versions (S1.3) | BETA is changed inside a recorded specification | specification address | R2 |
| 5 | endogenous activation (S1.3) | an operator switches the window, no event | ontology version not active | R1 |
| 6 | retained evidence (S1.4) | only the length of a tour is stored | the realization no longer matches the record | R2 |
| 7 | certification (S1.5) | a tour is appended after the budget is spent | criterion is false on replay | R2 |
| 8 | record, then activate | a new criterion judges before its event is recorded | criterion version not active | R1 |

The defects are built outside Z₀: each is a record Z₀ would not have written. The last column is
read from the check that failed (`replay.lost`), not asserted by the defect. In cases 1 and 6 the
verifier stops because it re-derives every candidate, which is more than R2 requires; the hash
link (case 1) and the re-judgment of the stored candidate (case 6) would stop it as well.

## Scope and limits

* The expression evaluator and the rules for function bodies restrict what a body can do, but they
  are not a security sandbox; specifications are trusted input.
* A body should not depend on the iteration order of a `set` of strings, which varies between
  processes: iterate over `sorted(...)` instead, so that replay in another process gives the same
  result.
* diskcache is atomic across processes on one machine. Redis gives atomic conditional writes from
  many machines through one primary; `durability: always` and `replicas: k` bound what a failure
  of the primary can lose, but Redis failover is not consensus. A system that must keep every
  admitted event when nodes fail needs the append to go through consensus (for example etcd). This is a choice of realization, not
  a new axiom (§4.7, §9.5).
* A boundary abstraction (§5.2) is supported through an occurrence bound to its invocation: the
  KPI profile, and abstractions with a declared source (`"sources"` in `system.json`; at present
  one kind, a seeded random source). Lineages read from outside the system are reported by
  `check`, and their readers wait.
* Every specification is admitted under τ_root, which checks that the new version is well formed
  and continues its lineage, whether the plan records it from a file or a candidate carries it in
  phase 3. Diagnosis and governing abstractions (§6.4, §8.5) are therefore ordinary abstractions
  whose criteria decide what they may change; none is among the examples here. An abstraction
  brought into being by a carried specification is evaluated in process, also when the others are
  served over HTTP, and a KPI profile already recorded does not count it.
* The verifier re-derives every candidate and then re-judges it, which is more than R2 requires.
  `verify --judgments` (`replay.verify(C, judgments_only=True)`) re-judges the recorded candidates
  without re-deriving them: it checks every judgment, and does not pay again for the ontologies
  (the search of a heuristic, for example). It does not check that a candidate follows from the
  record: of the eight defects it finds seven, and misses the third, whose draws were never
  recorded. The full replay remains the default.
* Not included yet: scheduling and abeyance
  abstractions (§5.2).

## References

1. Tarski, A.; Givant, S. *A Formalization of Set Theory without Variables*. American Mathematical
   Society Colloquium Publications, Vol. 41; American Mathematical Society: Providence, RI, 1987.
   https://doi.org/10.1090/coll/041
2. Škarić, M.; Ivanović, A.; Radenković, M.; Prokhorov, S.; Labus, A.; Radenković, B. *A Calculus of
   Execution for Systems of Interacting Binary Relations: Contextual Resolution, Separated
   Admission, and an Inseparable Execution Substrate*. Preprint, 2026. DOI to be added.
3. Ivanović, A.; Radenković, M.; Prokhorov, S.; Labus, A.; Radenković, B. Zero Tier Execution
   Substrate for Evolutionary Software Systems. *Systems* **2026**, 14, 547.
   https://doi.org/10.3390/systems14050547

Section, theorem, and table numbers in this repository refer to [2].

## License

MIT, see `LICENSE`.

## Notice

The substrate and the examples in this repository are a supplement to a scientific paper and are
provided as is (see the license); the authors accept no liability for their use.

"Zero-tier execution substrate" (ZTES), in the sense of tierless execution, is the name of a concept of
program execution defined in the paper. It is not a commercial product, and it is not connected with
ZeroTier, Inc. or its VPN and SDN networking products; the authors have no relation to that company.
