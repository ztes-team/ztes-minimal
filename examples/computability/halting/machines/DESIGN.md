# Halting and certified non-halting: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Base paper: Lemma 7 (§6.1), Theorem 4, Proposition 14. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** Five Turing machines, each a governed question. Three Busy Beaver champions halt, and the halting configuration is recorded. Two machines never halt, and a certificate is recorded that the criterion checks without search.

## 1. Problem

| m | Machine (bbchallenge notation; Z halts) | Answer |
|---|---|---|
| 1 | `1RB1LB_1LA1RZ`, the BB(2) champion | halts after 6 steps, 4 ones |
| 2 | `1RB1RZ_1LB0RC_1LC1LA`, the BB(3) champion | halts after 21 steps, 5 ones |
| 3 | `1RB1LB_1LA0LC_1RZ1LD_1RD0RA`, the BB(4) champion | halts after 107 steps, 13 ones |
| 4 | `1LB0RB_1LC0LC_0RA1RZ`, a cycler | never halts: configuration 6 equals configuration 0 |
| 5 | `1RB0LB_1RC1RA_1LB1RZ`, a translated cycler | never halts: from step 6 it repeats steps 0–6 two cells to the right |

Machines 4 and 5 have a halting transition, C1 → 1RZ, that they never take.

## 2. Decomposition into binary relations

    Step    = { ((M, c_k), c_k+1) : one transition of M from configuration c_k }
    Verdict = { ((M, c_0 … c_j), v) : v = halts, if c_j halts; v = never halts, with a certificate (i, j) }

Step is single-valued. Verdict is single-valued for the earliest certificate found, which is the
policy of the ontology. The criterion admits any correct certificate.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `run` | Step | the next configuration of M by one transition; ⊥ at a halting configuration, once a verdict is recorded, at the bound K = 200, or once the recorded configurations contain a certificate | that transition, against the recorded configuration before it | `run`, `verdict` |
| `verdict` | Verdict | halts, from a recorded halting configuration; or never halts, with the smallest i for which (i, j) is a certificate at the last configuration j: a search | the given halting configuration, or the given pair (i, j), checked without search | `run`, `verdict` |

Payloads: `{"m": 3, "k": 17, "state": "D", "head": -1, "lo": -3, "tape": [1, 1, 0, 1, 0]}`, and
`{"m": 4, "halts": false, "kind": "cycle", "i": 0, "j": 6, "steps": 6, "ones": 0}`. Versions 2–5
of both abstractions reuse the bodies of version 1 with the constants M and MACHINE. The table of
transitions is the derived value TRANS = table(MACHINE).

## 4. Design decisions and what they illustrate

* **Two kinds of certificate, both inductive invariants (Proposition 14).**
  * **cycle:** configuration j equals configuration i, so the computation from j repeats that from
    i forever.
  * **translated:** at step i every cell from the head to the right is blank; between i and j the
    head never moves left of its position at i; at j the state is the same, the head is further
    right, and every cell from it to the right is blank. The computation from j then repeats that
    from i shifted, forever.

  A certificate (i, j) shows that configuration j repeats configuration i, exactly or shifted into
  blank tape, with no halting configuration between them. By induction on the number of repetitions
  the computation from j repeats the steps i … j forever, so no future step halts (Proposition 14).
* **D2: the ontology searches, the criterion checks.** `verdict` searches the recorded
  configurations for a pair; its criterion checks the given pair only. A wrong pair, or a claim that
  a certified machine halts, is refused (tests).
* **A missing verdict is not a verdict.** `verdict` is ⊥ while neither a halting configuration nor a
  certificate is recorded. A machine without either would stop at the bound K with no verdict.
* **`run` stops at the first certificate.** Its ontology checks for one at every step, so the record
  ends at the same step under every schedule.
* **One regime per machine, and a named goal.** Each machine is a governed change (R1). An
  evolutive change ends a regime, so each machine is classified in its own regime. For the goal "a
  halting configuration of M is recorded" the champions are in 𝔗 and the certified machines in 𝔓.
  For the goal "a verdict is recorded" the same task terminates for every machine, 𝔗.
* **The class depends on the family of goals and on the regime.** For machine 5 and the goal
  "halts" the run is in 𝔓. Consider instead its unbounded simulation, a regime whose `run` records
  every configuration and never stops at a certificate, with the countable family "the record
  contains a configuration in which cell k holds a 1", k = 0, 1, 2, … . Each goal is persistent,
  since the record only grows, and each is established at a finite step, so that execution is in 𝔒.
  Here `run` stops at the first certificate: the execution is terminal, attains these goals only
  for k ≤ 2, and for this family is in 𝔓. An executable 𝔒 is `sqrt2-digits` (E7).

## 5. Plan

```
phase 1, phase 2   run and verdict v1 (machine 1)
phase 3            until terminal: 7 configurations, then the verdict
govern             run v2, verdict v2 (machine 2); phase 3
govern             … v3, v4, v5 (machines 3, 4, 5); each followed by phase 3
kpi                execution indicators, once, at the end
```

## 6. Expected end

151 configurations (7, 22, 108, 7 and 7), 5 verdicts, 183 events with the KPI step. Both
abstractions end in permanent wait. R2 replays the record.

## 7. Files

```
system.json                                           types Config, Verdict; constant K; derived TRANS; bindings configs, verdicts; plan; expect
lib.py                                                the machine, the two certificates, the check of a verdict, measure()
DESIGN.md
abstractions/run/{criterion, ontology}.v1.py          the bodies
abstractions/run/{criterion, ontology}.v{1–5}.json    M and MACHINE of the five machines, same bodies
abstractions/verdict/{criterion, ontology}.v1.py
abstractions/verdict/{criterion, ontology}.v{1–5}.json
abstractions/kpi/{criterion, ontology}.v1.{json,py}   the KPI abstraction
```

## 8. Execution indicators (KPI)

```
{"profile": 1, "machines": 5, "halting": 3, "certified": 2, "configurations": 151,
 "steps": [6, 21, 107, 6, 6], "ones": [4, 5, 13, 0, 2], "verdict_invocations": 84, "verdict_not_yet": 79}
```
