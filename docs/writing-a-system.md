# Writing a system for the substrate

This document belongs to the substrate. The examples that follow it are described separately in
[`examples/README.md`](../examples/README.md).

A system (an example) is a directory of JSON files and one design document. It contains no Python
code. The substrate loads it, checks it, records its specifications, and executes it.

```bash
python -m ztes new    examples/<system> --abstractions a,b   # a valid skeleton to start from
python -m ztes check  examples/<system>     # static check, nothing is executed
python -m ztes design examples/<system>     # the abstractions and their APIs
python -m ztes run    examples/<system>     # execute the plan, verify the record, compare with "expect"
python -m ztes run    examples/<system> --trace              # the same, showing every evaluation
```

A convenient way to work: `new`, then fill in DESIGN.md sections 1–3 (the problem, the binary
relations, the abstractions), then write the specifications, `check`, `run --trace` until the run
does what DESIGN.md says, and finally write "Expected end" and `"expect"`.

**Two forms of a specification.** You write specifications in a short *authoring form*: shared
types, constants and bindings are declared once, and the obvious fields are left out. When the
system is loaded, the substrate expands every specification into its *recorded form*: complete,
self-contained, addressed by its content. Only the recorded form enters the record C, is judged by
τ_root, and is replayed by R2, so the shortcuts never affect the guarantees.
`python -m ztes design <system> --full` shows the expanded form.

## 1. What a system must contain

```
examples/<system>/
  system.json                              required   abstractions, plan, expect; shared declarations
  DESIGN.md                                required   step 0: the design, for the reader
  abstractions/<name>/criterion.v1.json    required   Sτ, recorded in phase 1
  abstractions/<name>/ontology.v1.json     required   Sω, recorded in phase 2
  lib.py                                   optional   helper functions shared by the specifications
  abstractions/<name>/abstraction.json     optional   declarations shared by this abstraction
  abstractions/<name>/lib.py               optional   helper functions of this abstraction only
  abstractions/<name>/ontology.v1.py       optional   the body of ontology.v1 as a Python function
  abstractions/<name>/criterion.v2.json    optional   later versions, recorded by governed changes
  abstractions/<name>/ontology.v2.json     optional   …
```

* One directory per abstraction, named as in `system.json`.
* File names are `<role>.v<k>.json`, with `role` `criterion` or `ontology` and versions 1, 2, …
  without gaps. The abstraction, role and version come from the path.
* Every abstraction has `criterion.v1` and `ontology.v1`.

## 2. DESIGN.md: the method, written down

DESIGN.md records step 0. It opens with one line that names the place in the paper and one
paragraph, **What this example adds**, that tells a reader why to open it. Then come these
sections, in this order (see [`examples/sqrt2/DESIGN.md`](../examples/sqrt2/DESIGN.md)):

1. **Problem.** What is to be computed or maintained, in plain terms.
2. **Decomposition into binary relations.** The problem as relations R ⊆ X × Y. Say what the left
   component X is (it will be read from the record) and what the right component Y is (it will be
   the payload of an admitted event).
3. **Lifting: the abstractions.** One abstraction per relation, in a table with columns: abstraction,
   relation, ontology (what it proposes, and when it is ⊥), criterion (what it admits), horizon (the
   lineages it reads).
4. **Design decisions.** What the design illustrates or guarantees, e.g. why no selector is needed
   (D1), what the criterion checks independently of the ontology (D2), how abstractions interact
   only through C.
5. **Plan.** The plan steps and any planned governed change, with the reason for it.
6. **Expected end.** The admitted values, which abstractions end closed and which in permanent wait,
   the number of events in the record. The same facts go into `"expect"` in `system.json`, where
   the substrate checks them.
7. **Files.** The list of files.
8. **Execution indicators (KPI).** What the KPI step records at the end: the profile (invoked,
   admitted, Not Yet, false for each abstraction) and, if the system has one, its own indicators.

## 3. system.json

```json
{
  "system": "dedekind-cut",
  "title": "Computable Dedekind cut for √2 …",
  "abstractions": ["denominators", "bounds", "intervals"],

  "types":     {"Bound": {"record": {"n": "integer", "d": "integer", "a": "integer"}}},
  "constants": {"N": 4},
  "bindings":  {"k": {"from": "$self", "select": "count"}},

  "plan": [
    {"phase": 1},
    {"phase": 2},
    {"phase": 3},
    {"govern": ["intervals/ontology.v2"], "note": "why the change is made"},
    {"phase": 3}
  ],
  "expect": {
    "events": 23,
    "states": {"denominators": "closed", "bounds": "wait", "intervals": "wait"},
    "values": {"bounds": [{"n": 0, "d": 1, "a": 1}, …]}
  }
}
```

| Field | Required | Meaning |
|---|---|---|
| `system` | yes | short name |
| `title` | no | one line shown in the output |
| `abstractions` | yes | the abstractions of the system; this order is also the initial agenda order |
| `types` | no | named types, usable wherever a type is expected |
| `constants` | no | named JSON values; a specification that uses one receives it automatically |
| `bindings` | no | named context bindings; `"$self"` in `from` means the abstraction that uses it |
| `derived` | no | named expressions over constants and helper functions, computed once per specification version, e.g. `"D": "matrix(XY, N)"` |
| `plan` | no | steps executed in order; default `[{"phase": 1}, {"phase": 2}, {"phase": 3}]` |
| `expect` | recommended | the expected end, checked after `run`: `events`, `states` (`closed`, `wait`, `wait-external`), `values` (the payloads admitted by an abstraction, in order). If a result depends on the order of invocations, `any_schedule` inside it states what holds under every order: `events`, `values`, and `last` (abstraction → fields of its last admitted value); see [distribution.md](distribution.md) |
| `admission_limit` | no | the most admissions one phase-3 step may make (default 10,000), a guard against criteria that never close |

`abstractions/<name>/abstraction.json` may declare `types`, `constants` and `bindings` for one
abstraction; they override the system-level declarations of the same name.

Plan steps:

| Step | Effect |
|---|---|
| `{"phase": 1}` | record `criterion.v1` of every abstraction (no evaluation) |
| `{"phase": 2}` | record `ontology.v1` of every abstraction, bound to its admitted criterion (no evaluation) |
| `{"phase": 3}` | execute until terminal |
| `{"phase": 3, "max_admissions": k}` | execute at most k admissions, then go on with the plan |
| `{"govern": ["a/criterion.v2", …]}` | record new versions; the changed abstractions are evaluated again |

Any step may carry `"note"`, printed when the step starts.

## 4. A specification

In the authoring form a criterion and an ontology look like this
([`examples/dedekind-cut`](../examples/dedekind-cut)):

```json
{
  "note": "[τ] a = ⌊√2·d⌋ for a recorded denominator d, checked by squares",
  "inputs": {"context": ["k", "dens"], "candidate": {"name": "w", "type": "Bound"}},
  "body": {
    "recorded": "{'n': w['n'], 'd': w['d']} in dens",
    "result": "w['n'] == k and recorded and w['a'] ** 2 <= 2 * w['d'] ** 2 < (w['a'] + 1) ** 2"
  }
}
```

```json
{
  "note": "[ω] a = isqrt(2d²) for the k-th recorded denominator; ⊥ while it is not recorded",
  "inputs": {"context": ["k", "den"]},
  "returns": "Bound",
  "body": {"result": "{'n': k, 'd': den['d'], 'a': isqrt(2 * den['d'] ** 2)}"}
}
```

| Field | Criterion (phase 1) | Ontology (phase 2) |
|---|---|---|
| `inputs.context` | bindings (below) | bindings (below) |
| `inputs.candidate` | `{"name": …, "type": T}`: how ω is passed | (none) |
| `returns` | (implied: `"boolean"`) | the type T of ω |
| `body` | named expressions; `result` is the judgment | named expressions; `result` is ω, or `None` for ⊥ |
| `note` | optional: a comment for the reader | optional: a comment for the reader |

Filled in by the substrate when it expands the file: `abstraction`, `role`, `version` (from the
path), `returns: "boolean"` and `total: true` for a criterion, `partial: true` for an ontology,
`criterion` (the address of the admitted criterion, bound in phase 2), the used `constants`, and
the declared types and bindings that the file names.

JSON has no comments, so a specification, a binding (also a declared one) and the candidate may
carry `"note"`: a comment for the reader, removed before the specification is recorded. The
examples begin each note with the axis the specification belongs to, `[τ]` for a criterion and
`[ω]` for an ontology, and mark comments in function bodies the same way.

### Context bindings

Every name the body uses, other than the candidate, the constants, and the names the body defines
itself, is a binding. `context` is either an object of bindings or a list of declared binding names
(`["k", "den"]`). A binding is written in place or names a declared one (`"k": "k"`):

```json
"name": {"from": "a" | ["a", "b"], "select": "...", "type": T, "where": "expr", "default": v}
```

| Field | Meaning |
|---|---|
| `from` | the lineage(s) read. The union over both specifications is the abstraction's **event horizon**. A lineage that is not an abstraction of the system is **external**. |
| `select` | `last` (latest value), `first`, `one` (the single qualifying value; more than one is an error), `all` (list of values), `count`, `exists`, `map` (below) |
| `window` | with `select: "all"`: only the last K qualifying events are read (K an integer or the name of a constant). Older events stay in C; they are simply not read |
| `type` | how payloads are decoded; default `json` |
| `where` | optional filter over `x`, one decoded value; it may also use the constants and the bindings declared **before** it, e.g. `"where": "x['n'] == k"` |
| `default` | the value of `last`/`first`/`one` while no event qualifies, written as a payload of type T |

Without a default, `last`/`first`/`one` with no qualifying event make the realization **undefined
(⊥)**: the abstraction waits for an event in its horizon. In a criterion every such binding needs a
default, because τ must be total.

### The complete horizon comes first: `requires`

An ontology is evaluated only on a complete horizon: if an event it needs is not in Cⁿ, the result
is Not Yet and nothing is computed. A binding without a default says this for one event. When the
ontology needs more than that, say it in the specification:

```json
"constants": {"N": 7, "Q": [0, 1, 2, 3, 4, 5, 6], "NEEDED": 192},
"requires":  {"dp": "NEEDED"}
```

`requires` maps a lineage of the horizon to the number of its events that must exist (a number, or
the name of a constant; `"$self"` is the abstraction itself). It is decided by counting, before
any binding is read. Without it `tour` of `examples/tsp` would run its body after each of the 448
subproblems only to find that they are not complete.

An invocation that appends nothing therefore has one of three grounds, and the summary of a run
counts them separately:

| Ground | What happened | Cost |
|---|---|---|
| Not Yet, horizon | a required event is not in Cⁿ | none: the body is not evaluated |
| Not Yet, body | every required event exists; the body, computed on their content, yields no candidate (⊥) | one evaluation of the ontology |
| τ false | a candidate exists and the criterion refuses it on this prefix | the ontology and the criterion |

The second and third depend on what the events say, not on whether they exist, so they can only
be found by computing. The agenda repeats them only when a lineage of the horizon gains an event.
Use `requires` for every condition that is a matter of existence; a large "body" column in the
summary shows where one may be missing.

### Map bindings: the record as a lookup table

When a body needs to look up recorded values by a key, as a memo table does, declare a map instead
of rebuilding a dictionary from `all` at every invocation:

```json
"cost": {"from": "dp", "select": "map", "type": "Entry", "key": "(x['mask'], x['j'])", "value": "x['cost']"}
```

The body receives a read-only mapping `{key: value}` (`value` defaults to the whole decoded event).
The substrate keeps it in the index of the record and extends it with each new event, so its cost
does not grow with the length of the lineage. Two events with the same key are an error. Because
the map is shared between invocations, `key`, `value` and `where` may use `x`, constants, derived
values and helper functions, but not other bindings; τ_root checks this. Values in a map are
immutable (lists become tuples).

### Types

| Type | Payload in C | Value in the body |
|---|---|---|
| `integer` | `5` | `5` |
| `rational` | `"3/2"` | `Fraction(3, 2)` |
| `boolean` | `true` | `True` |
| `text` | `"abc"` | `"abc"` |
| `json` | any JSON | as is |
| `{"list": T}` | `[…]` | list of T |
| `{"record": {"f": T, …}}` | `{"f": …}` | dict with exactly these fields |
| a declared name, e.g. `"Bound"` | as its definition | as its definition |

A result of the wrong type stops execution with an error that names the specification. Note that
`a / b` on integers gives a float, which is neither an integer nor a rational: write
`Fraction(a, b)` or `a // b`.

### Body

`body` is an ordered object of named expressions. Each is one Python expression and may use the
bindings, the candidate, the constants, the names defined before it, and only these functions:
`Fraction, gcd, isqrt, floor, ceil, abs, min, max, sum, len, sorted, range, all, any, prod, set`.
Comprehensions and generator expressions are allowed. There is no I/O, clock, or randomness, so
every result is determined by the record (S1.2, S1.4). A further pure function is added in one
place, `SAFE` in `ztes/model/language.py`.

### Body as a Python function

When the logic of a body needs loops and intermediate variables, write it as one function in a file
next to the JSON, with the same name and `.py` (e.g. `ontology.v1.py`), and leave `body` out of the
JSON. The parameters are what the function receives: declared bindings, the candidate (for a
criterion), and constants. From [`examples/factorization`](../examples/factorization/abstractions/factor):

```python
def omega(n, primes, prev):
    if n == prev["n"]:
        return None                                  # already factored: nothing to propose
    g = gcd(n, prev["n"])
    ...
    if r != 1:
        return None                                  # a factor lacks a certificate: wait for primes
    return {"n": n, "factors": sorted(from_cert + from_primes),
            "reused": prev["n"] if g > 1 else 0, "gcd": g}
```

Rules, checked by `check` and by τ_root before the specification is recorded:

* exactly one top-level `def`; plain parameters only;
* statements: assignment, `if`, `for` over a finite iterable, `return`, `pass`, `continue`, `break`,
  and expression statements such as `xs.append(x)`;
* no `while`, `try`, `with`, `raise`, `import`, `global`, `lambda`, nested `def`, `class`, `del`,
  `assert`; no name or attribute beginning with `_`; no recursion;
* every name is a parameter, a local variable, or one of the allowed functions.

The source text becomes the recorded body, so R2 replays exactly the function that was judged.
A later version that changes only constants can reuse the body of an earlier one with
`"body_file": "ontology.v1.py"` in its JSON (see [`examples/tsp`](../examples/tsp)).
Iterate over `sorted(...)` rather than over a set of strings, whose order varies between processes.

### Helper functions (lib.py) and derived values

Logic used by several specifications (a distance, the children of a search node, a bitmask) goes
into `lib.py` next to `system.json`, as plain functions under the same rules as a function body. A
helper may call helpers defined before it, never itself or a later one. From
[`examples/tsp`](../examples/tsp/lib.py):

```python
def dist(XY, a, b):
    return abs(XY[a][0] - XY[b][0]) + abs(XY[a][1] - XY[b][1])

def matrix(XY, N):
    return [[dist(XY, a, b) for b in range(N)] for a in range(N)]
```

Values that depend only on constants are declared once as derived values in `system.json`
(`"derived": {"D": "matrix(XY, N)"}`) and used by name, in a body or as a parameter of a body
function. They are computed once per specification version, not at every invocation, and they are
immutable.

A specification receives a copy of exactly the helpers, derived values and constants it uses, and
of those they use in turn: its recorded form still depends on nothing outside itself, so R2
replays it unchanged. Helpers receive what they need as arguments; they do not read constants by
name. `python -m ztes design <system> --full` shows what each specification received.

### Seeing what happens: trace and explain

`run --trace` prints, after every invocation, the bindings, the intermediate values of the body, ω
or ⊥, and the judgment. `explain DIR N` does the same for one event of a kept record, from its
prefix alone, e.g. why the second payment of [`examples/payment`](../examples/payment) was admitted:

```
event 17: exec of transfer
  transfer/criterion.v1
    binding  overridden = True
    passed = False
    τ = True
```

### Execution indicators: a KPI abstraction

Indicators are designed like the rest of the system, as an abstraction. Add `"kpi": "kpi"` to
`system.json`, a step `{"kpi": true}` to the plan where the indicators are wanted (usually at the
end), and the specifications in `abstractions/kpi/`. The declared bindings `profile` (the latest
counts of outcomes: I, A, U, H, F for each abstraction; H is the part of U decided by the horizon alone) and `profiles` (how many are recorded) are
available to it; anything else it reads from the record like any abstraction. From
[`examples/tsp`](../examples/tsp/abstractions/kpi):

```python
def omega(done, tours, profile, profiles, kpis):
    if profiles == 0 or kpis >= profiles:
        return None                                    # ⊥: nothing new to measure
    return measure(done, tours, profile, profiles)     # in lib.py
```

The criterion admits one measurement per profile, each indicator equal to its definition. Many ⊥
for few admissions (U against A) suggests a horizon wider than the abstraction needs. A heuristic
agent reads the `kpi` lineage and adapts; `run --metrics` prints the latest indicators.

### When a specification fails

An exception inside a body (an index out of range, a wrong type) is a defect of the specification.
`run` stops and names it, e.g.

```
error in a specification, execution stopped:
   upper/ontology.v1, body 'result': IndexError: list index out of range
```

The record up to that point is kept and remains verifiable.

A specification that is malformed (a missing default in a criterion, an undeclared name, a version
gap) does not get that far: `check` and τ_root refuse it before it is recorded and say why, e.g.

```
problem: lower/criterion.v2: binding 'lower': a criterion binding with select last, first or one
         needs a default (τ is total)
```

## 5. Rules that make a system terminate

* An abstraction is evaluated again only when an event appears in its horizon or its specification
  changes. If its criterion admits the same kind of candidate forever, the system never becomes
  terminal; the substrate stops at an admission limit and says so.
* Make each criterion require progress (a strictly smaller interval, a strictly larger count) and a
  bound or goal at which it becomes false.
* A missing default in an ontology binding is the way to say "wait for this lineage".

## 6. Inputs from the environment are an ontological matter

Most of the examples are closed: every candidate is computed from the record. A system that receives
data from outside (requests, sensor readings, messages) does not need a new mechanism in the
substrate. Where a candidate comes from is decided by the ontological specification: the ontology
declares the external input as part of its API, next to the bindings it reads from C, and its body
remains a function of both. The candidate is then bound to the invocation (§1.4, §3.2.2). The form
below, with a declared channel, is not executed by the present substrate; it shows how such an
ontology is specified.

What the substrate does execute is the plain boundary abstraction (§5.2): an ontology
`{"boundary": true, "returns": T, "inputs": {"context": {}}}` has no body, and its candidate is the
occurrence bound to the invocation. Two things use it: the `profile` of the execution indicators,
and abstractions with a declared source in `system.json`,

```json
"sources": {"draw": {"random": {"seed": 1, "size": 11, "below": 1000000}}}
```

which gives every phase-3 invocation of `draw` a list of 11 integers below 1,000,000 (the example
`aco-draw`). The seed belongs to the environment; what was drawn is in C, and replay reads it there.

```json
{
  "inputs": {
    "context": {"seen": {"from": "requests", "select": "count"}},
    "invocation": {
      "name": "msg",
      "channel": "payments-api",
      "type": {"record": {"id": "integer", "from": "text", "to": "text", "amount": "integer"}}
    }
  },
  "returns": {"record": {"id": "integer", "from": "text", "to": "text", "amount": "integer"}},
  "body": {"result": "msg if msg is not None and msg['id'] == seen + 1 else None"}
}
```

* **The input is part of the API.** `inputs.invocation` declares the channel and the type of the
  external datum, as `inputs.context` declares what is read from C.
* **D1 still holds.** One invocation yields at most one candidate; without a bound message, or with
  one that is not next in order, the result is ⊥ (Not Yet).
* **D2 still holds.** The criterion of `requests` (consecutive id, amount > 0, from ≠ to) knows
  nothing of the channel; it judges the candidate only.
* **R2 rests on the recorded candidate.** R2 requires that a judgment be reproduced from the
  preceding record, the *original recorded candidate*, and the specification addresses (§1.3). An
  external message cannot be read again, and need not be: the admitted payload is the evidence.
  The present verifier also re-derives each candidate, which is correct only for ontologies that
  compute from the record; for an ontology with `inputs.invocation` the exact check is the
  criterion applied to the recorded candidate.

## 7. Checklist

- [ ] `DESIGN.md` says in its first lines what the example adds, and has the eight sections, including the decomposition into binary relations and the indicators.
- [ ] Every abstraction listed in `system.json` has a directory with `criterion.v1` and `ontology.v1`.
- [ ] Shared types, constants and bindings are declared once, in `system.json` or `abstraction.json`.
- [ ] Logic used by more than one specification is in `lib.py`; values that depend only on constants
      are `derived`; lookups by key over a lineage are `map` bindings.
- [ ] Every name used in a body is a binding, the candidate, a constant, or a name defined earlier.
- [ ] Every criterion binding with `last`/`first`/`one` has a default.
- [ ] Each specification has a `"note"` saying, in one line, what it proposes or admits.
- [ ] The plan ends with `{"kpi": true}`; indicators specific to the problem are a `kpi` abstraction.
- [ ] Every criterion requires progress and eventually becomes false (or the wait is intended).
- [ ] `system.json` has `"expect"` matching "Expected end" in `DESIGN.md`.
- [ ] Bodies written as functions iterate over `sorted(...)`, not over sets of strings.
- [ ] `python -m ztes check` reports OK.
- [ ] `python -m ztes run` ends terminal, R2 reports OK, and Expect reports OK.
