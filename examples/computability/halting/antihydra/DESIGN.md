# Antihydra: the frontier: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md). Base paper: Lemma 7 (§6.1), Theorem 4, Definition 6. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** A computation whose halting no one has decided. The record shows 1,000
iterations of its recurrence (not steps of the machine) and no verdict, and no finite record could
show one either way.

## 1. Problem

Antihydra is a machine with six states, `1RB1RA_0LC1LE_1LD1LC_1LA0LB_1LF1RE_---0RA`, found among the
holdouts of BB(6) in 2024. bbchallenge has shown that it halts if and only if the following rules
ever give b = −1:
* start with a = 8, b = 0;
* at each step, b grows by 2 if a is even and falls by 1 if a is odd;
* then a becomes a + ⌊a/2⌋.

Source: https://bbchallenge.org/antihydra, and The bbchallenge Collaboration, *Determination of the
fifth Busy Beaver value*, arXiv:2509.12337, Appendix C. The equivalence of the rules with the
machine is their lemma, cited and not checked here. This system executes the rules.

## 2. Decomposition into binary relations

    Rule = { ((k, a, b), (k+1, a + ⌊a/2⌋, b + 2 if a is even else b − 1)) : b ≠ −1 }
    Halt = { ((k, a, b), k) : b = −1 }

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `rule` | Rule | the next step from the last recorded one; ⊥ once b = −1 | that step, against the step before it | `rule` |
| `halt` | Halt | the goal, once a recorded step has b = −1; ⊥ before | once, at that step | `rule`, `halt` |

Payload: `{"k": 12, "a": 1021, "b": 12}`.

## 4. Design decisions and what they illustrate

* **One branch, never 𝔚.** The rules are deterministic. If b ever reaches −1 the run is in 𝔗;
  otherwise the goal is False at every prefix and the run is in 𝔓. No prefix keeps the goal
  reachable without taking it.
* **A missing verdict is not a verdict.** `halt` is ⊥ at every prefix of the window. That is a
  status of what is recorded, not evidence that the machine never halts.
* **Exact integers.** After 1,000 iterations a has 177 digits, recorded exactly.

## 5. Plan

```
phase 1, phase 2   rule and halt v1
phase 3            a window of 1,001 admissions: step 0 and 1,000 iterations
kpi                execution indicators, once, at the end
```

## 6. Expected end

Step 0 and 1,000 iterations, and no goal: 1,012 events with the KPI step. The run is paused, not terminal. R2
replays the record.

## 7. Files

```
system.json                                           types Step, Halt; bindings steps, last, halts, history; plan; expect
lib.py                                                the rules, digits(), measure()
DESIGN.md
abstractions/rule/{criterion, ontology}.v1.{json,py}
abstractions/halt/{criterion, ontology}.v1.{json,py}
abstractions/kpi/{criterion, ontology}.v1.{json,py}   the KPI abstraction
```

## 8. Execution indicators (KPI)

```
{"profile": 1, "steps": 1000, "b": 497, "even": 499, "odd": 501, "lowest_b": 0, "digits_of_a": 177,
 "halted": false}
```

b grows by about one half per step on average, so the window moves away from −1. This is why
bbchallenge calls Antihydra "probviously" non-halting: a heuristic, not a proof.
