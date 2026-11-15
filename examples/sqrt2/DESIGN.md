# √2 by bisection: design (step 0)

*Paper: §8.2 (a simplified variant). Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** The smallest system: two abstractions, one record, and one governed change. Start here.

This is a simplified variant of §8.2, chosen as the shortest introduction. The construction of the
paper itself, with three streams, is the example `dedekind-cut`.

Design happens before execution and outside the substrate. Its result is the set of specification
files in `abstractions/`. Phases 1 and 2 only record them in C; phase 3 evaluates them. Nothing
designed here is active until its event is admitted.

## 1. Problem

Construct √2 as a Dedekind cut: a sequence of rational intervals [l, u] with l² < 2 < u², each
half as wide as the previous one, starting from [1, 2] (cf. §8.2). Stop when the interval is narrow
enough.

## 2. Decomposition into binary relations

Write I for the set of rational intervals and ℚ for the rationals. The problem is two relations from
intervals to rationals:

    Lower = { ([l, u], m) : m = (l + u)/2 and m² < 2 }  ⊆ I × ℚ
    Upper = { ([l, u], m) : m = (l + u)/2 and m² > 2 }  ⊆ I × ℚ

Since m² ≠ 2 for every rational m, for each interval exactly one of the two relations has a
nonempty fiber. A pair ([l, u], m) in Lower moves the lower end to m; a pair in Upper moves the
upper end.

## 3. Lifting: the abstractions

Each relation becomes one abstraction. The left component, the current interval, is not stored as
a value: it is read from the record as the last admitted `lower` and `upper` (defaults 1 and 2).
The right component, m, is the payload of the admitted event.

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `lower` | Lower | the midpoint m of [lower, upper], **defined only if m² < 2**, else ⊥ | w² < 2 and lower < w < upper | `lower`, `upper` |
| `upper` | Upper | the midpoint m of [lower, upper], **defined only if m² > 2**, else ⊥ | w² > 2 and lower < w < upper | `lower`, `upper` |

Both specifications read the same two bindings, declared once in `system.json`:
`{"from": "lower", "select": "last", "type": "rational", "default": "1"}` and the same for `upper`
with default `"2"`.

## 4. Design decisions and what they illustrate

* **No selector (D1).** For each context exactly one ontology is defined. Which bound moves next is
  decided by the record, not by a scheduler; the order in which the substrate tries the
  abstractions does not matter.
* **Separate criterion (D2).** The criterion does not repeat the ontology. It checks what an
  admitted value must satisfy (the correct side of the cut, and a strictly smaller interval),
  whatever produced the candidate.
* **No direct communication.** `lower` and `upper` never call each other. Each sees the other only
  through the shared record (context-mediated interaction, §4.1.4).

## 5. Plan and planned evolution

```
phase 1          criteria v1
phase 2          ontologies v1
phase 3          two admissions (3/2, 5/4), then pause
govern           criteria v2: add  upper - lower > 1/64
phase 3          until terminal
```

Criterion v2 stops the refinement once the interval is narrow enough. It is recorded during
execution as a new phase-1 event. The ontologies are not changed, which shows that admission can
evolve independently of realization (Proposition 15).

## 6. Expected end

Six bounds are admitted: 3/2, 5/4, 11/8, 23/16, 45/32, 91/64 (width 1/64). Then `lower` obtains
181/128, but its criterion v2 is false, so `lower` is **closed**. The midpoint belongs to `lower`,
so `upper` is in **permanent wait**. The agenda is empty and the system is terminal. The record has
13 events, 16 with the KPI step at the end (the profile and its two specifications), and R2
replays it.

## 7. Files

```
system.json                            abstractions, bindings lower and upper, plan, expect
DESIGN.md                              this design
abstractions/lower/criterion.v1.json   phase 1
abstractions/lower/ontology.v1.json    phase 2 (bound by the substrate to the admitted criterion)
abstractions/lower/criterion.v2.json   governed change
abstractions/upper/…                   the same for upper
```

## 8. Execution indicators (KPI)

The plan ends with one KPI step. The profile it records:

```
lower: invoked 5, admitted 3, Not Yet 1, false 1
upper: invoked 5, admitted 3, Not Yet 2, false 0
```

Of ten invocations six leave an event. Three ended at Not Yet (the realization was undefined on that prefix) and one at false: the judgment that closes `lower`.
