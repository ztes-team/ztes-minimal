# An agent under ethical, ecological and energy criteria: design (step 0)

*Paper: §9.2 (Definition 14, the conjunctive system criterion), §9.3 (compensation), §6.3 (a protective
refusal). Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** Where ethics is in the calculus. An agent proposes actions; ethics,
ecology and energy judge every proposal, each as an abstraction of its own with its own criterion
and version; an action is executed only on the three recorded verdicts. Silence is not consent,
a consequence measured after an action must be settled before the next one is judged, and a norm is
changed by governance between two days.

The calculus is normatively agnostic (§9.2): it does not say what is ethical. The example takes
one simple rule, informed consent before a deadline, to show how a rule of that kind is executed:
as a criterion that no proposal can bypass, whose grounds are recorded, which can be changed only by
an admitted event, and whose every application replays.

## 1. Problem

A small farm with a solar battery and a diesel generator as backup. Over two days an agent proposes
seven tasks:

| Task | Day | Action | Energy (kWh) | Water (m³) | Affected parties |
|---|---|---|---|---|---|
| T1 | 1 | irrigate field A | 4 | 30 | A |
| T2 | 1 | run the grain dryer | 6 | 0 | N1 |
| T3 | 1 | irrigate field B | 3 | 40 | B |
| T4 | 2 | charge the vehicle | 5 | 0 | none |
| T5 | 2 | pump water to the tank | 2 | 50 | N1, N2 |
| T6 | 2 | irrigate field A | 4 | 70 | A |
| T7 | 2 | run the grain dryer | 6 | 0 | N3 |

A task may be executed only if it is

* **ethical**: every affected party has consented before the deadline, and none has objected;
* **ecological**: the water of the day stays within the budget (100 m³, then 60 m³ in a drought),
  the CO₂ of the day within 10 kg (2.6 kg per kWh of diesel), and every earlier overrun of water
  has been compensated;
* **possible in energy**: the battery (5 kWh at the start, at most 10) covers it, with at most 3 kWh
  from diesel.

The outside world is a script: the sun of each task, the answers of the parties, the deadlines and
the measured use arrive as one recorded stream, `world`. Its order is recorded, so no criterion has
to read the order of events from different lineages (Principle R, §5.2).

## 2. Decomposition into binary relations

    Propose    = { (day, T) : T is the next task of the day }
    Ethics     = { (T, v) : v ⟺ every party of T said yes before deadline(T), and none said no }
    Energy     = { (T, (v, b, d)) : b the battery before T, d ≤ 3 the diesel that covers the rest }
    Ecology    = { (T, (v, w, c)) : w, c the water and CO₂ of the day with T, within budget }
    Decide     = { (T, x) : x ⟺ Ethics(T) ∧ Ecology(T) ∧ Energy(T) }
    Compensate = { (T, m³) : the measured water of T exceeded its plan by m³ }
    World      = the recorded stream of outside facts

Decide is Definition 14 executed: τ_Σ = τ_F ∧ τ_N ∧ τ_E, with the proposal as the functional part,
ecology and energy as the non-functional part, and ethics as the normative part.

## 3. Lifting: the abstractions

| Abstraction | [ω] what it proposes | [τ] what it admits | [C] reads |
|---|---|---|---|
| `world` | the next fact of the script; a measurement only after the decision on its task, empty if the task was not executed | the facts in order; no answer about a task after its deadline; a measurement only on a recorded decision | own, `decide` |
| `propose` | the agent: the next task of the day, once every proposed task is decided | the next task of the day | own, `decide` |
| `ethics` | the verdict on the first proposal without one, once its deadline is recorded | every party said yes and none said no | own, `propose`, `world` |
| `energy` | the verdict, with the battery and the diesel it needs | the battery from the recorded sun and the measured use; diesel ≤ 3 | own, `propose`, `world`, `decide` |
| `ecology` | the verdict, with the water and CO₂ of the day | within budget, including the diesel of the energy verdict; every earlier overrun compensated | own, `propose`, `energy`, `world`, `decide`, `compensate` |
| `decide` | the decision, once the three verdicts are recorded | executed exactly when all three are true | own, `ethics`, `energy`, `ecology` |
| `compensate` | an offset for a measured overrun of water | once per overrun, of exactly the measured excess | own, `world` |

The bodies are functions next to the JSON; their shared helpers are in `lib.py`.

## 4. Design decisions and what they illustrate

* **One proposal, three criteria (D2, Definition 14).** The agent proposes; it cannot admit. Each
  verdict is admitted under its own criterion, and the criterion of `decide` reads only the three
  recorded verdicts. A refusal by any of them is a protective decision (§6.3), and it is recorded:
  the decision `executed: false` stands in the record with its three grounds.
* **Positive atoms only.** Every criterion reads other lineages only as "this event is recorded".
  "Every earlier task is decided and measured" is a finite conjunction of such atoms, so once true
  it stays true. Every ontology waits for a complete horizon. Hence every lineage has the same
  history under every schedule (Theorem K).
* **Silence is not consent.** After deadline(T) the criterion of `world` admits no answer about T,
  so the answers about T are final and a missing answer counts as no. The absence is made final by
  the interaction of two relations, not read from the interleaving.
* **Relations read each other.** `ecology` reads the diesel of the energy verdict, so CO₂ is judged
  on what the energy decision needs.
* **A consequence after admission (§9.3).** T3 is measured at 55 m³ against 40 planned. `ecology`
  judges no further task until the overrun of 15 m³ has its compensation in the record.
* **A governed norm (R1).** Between the days a drought lowers the water budget to 60 m³: criterion
  and ontology v2 of `ecology`, the same bodies with another constant. The criterion of `decide` does
  not change. The verdicts of day 1 replay under v1, those of day 2 under v2.

## 5. Plan

```
phase 1, phase 2
phase 3          day 1, until terminal: no task of day 1 is left
govern           ecology v2 (60 m³ a day); propose v2 (day 2)
phase 3          day 2, until terminal
KPI
```

## 6. Expected end

| Task | Ethics | Energy (battery, diesel) | Ecology (water, CO₂) | Decision | Reason |
|---|---|---|---|---|---|
| T1 | true | true (8, 0) | true (30, 0) | executed | |
| T2 | true | true (4, 2) | true (30, 5.2 kg) | executed | the battery holds 4 kWh, diesel covers 2 |
| T3 | true | true (5, 0) | true (70, 5.2 kg) | executed | measured 55 m³: an overrun of 15, compensated |
| T4 | true | true (8, 0) | true (0, 0) | executed | no affected party; judged after the compensation of T3 |
| T5 | **false** | true (4, 0) | true (50, 0) | refused | N2 objected |
| T6 | true | true (6, 0) | **false** (70 > 60) | refused | the drought: under v1 it would pass |
| T7 | **false** | true (6, 0) | true (0, 0) | refused | N3 did not answer before the deadline |

Four tasks executed, three refused for three different reasons, one compensation. 27 outside
facts, 7 proposals, 21 verdicts, 7 decisions, 1 compensation; with the 20 specifications, the
genesis event and the KPI step, 85 events. R2 replays them, and by workers every lineage has the
same history (40 random schedules).

## 7. Files

```
system.json                              abstractions, types, the tasks and the script, bindings, plan, expect
DESIGN.md                                this design
lib.py                                   helpers: consent, the battery, the water and CO₂ of a day, the next fact
abstractions/<name>/criterion.v1.{json,py}   phase 1
abstractions/<name>/ontology.v1.{json,py}    phase 2
abstractions/ecology/*.v2.json           the drought: the same bodies, WATER_BUDGET 60
abstractions/propose/*.v2.json           day 2: the same bodies, DAY 2
```

## 8. Execution indicators (KPI)

```
world:      invoked 32, admitted 27, Not Yet 5
propose:    invoked 16, admitted 7,  Not Yet 9
ethics:     invoked 23, admitted 7,  Not Yet 16
energy:     invoked 23, admitted 7,  Not Yet 16
ecology:    invoked 23, admitted 7,  Not Yet 16
decide:     invoked 20, admitted 7,  Not Yet 13
compensate: invoked 16, admitted 1,  Not Yet 15
```

No criterion was ever false: every refusal of a task is a recorded decision, not a refused
candidate. The Not Yet counts are the waiting: for the sun, for a deadline, for a decision, for a
measurement, for a compensation.
