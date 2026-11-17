# Specifications proposed in execution: design

*Status: implemented (§5), after the optimizations that keep every record identical (§7). How to
write such a system: [writing-a-system.md](writing-a-system.md#specifications-carried-by-a-candidate).*

## 1. What is proposed

Today a specification enters the record in one way: the plan reads it from a JSON file and Z₀
admits it under τ_root (phases 1 and 2, and the plan step `govern`). The proposal adds a second way:
an abstraction proposes specifications in phase 3, as part of its candidate, and they are admitted
by the same rule. Both ways give the same thing in C: an admitted version, active from its event on
(S1.3).

This is R1 taken literally: governance is internal to execution. A system can then change its own
ontologies and criteria, and bring new abstractions into being, through admitted events that replay.

## 2. Principles

1. **Z₀ knows no kinds of abstraction.** There is no "governing abstraction" in ZTES. Every
   abstraction has an ontology that proposes and a criterion that judges; any of them may propose
   specifications. Z₀ treats them all alike.
2. **Who may do what is decided by criteria.** The criterion of the proposing abstraction, the one
   active in Cⁿ, is the authority in force: it judges the whole candidate, the specifications it
   carries included. It may be any system of relations evaluated before admission, and it may read
   a policy that is itself recorded, and changed, by admitted events. ZTES declares no scopes and
   forbids nothing, a change of the proposer's own specifications included: if the criterion in
   force admits it, it holds.
3. **τ_root stays the only fixed check.** It belongs to the zeroth tier with Axiom 0. It knows
   nothing of the domain, only the form of a specification and the continuity of its lineage
   (versions 1, 2, … without gaps; an ontology bound to the active criterion). Without it, which
   version is active would not be defined.
4. **Everything is in the record.** A carried specification is complete and self-contained, as one
   loaded from a file is after authoring: its constants, derived values and library are in it. A
   proposer may compose it or take it from its own constants; it may not read files in execution.
5. **What exists keeps its meaning.** Loading from files, the plan, `govern`, and every record made
   so far are unchanged.

## 3. The mechanism

**Carrying.** An ontology whose return type is a record may declare one field of type
`{"list": "specification"}` (a new basic type: a JSON object, read and written as it is). The
specifications in that list, in its order, are carried by the candidate. An empty list carries
nothing; a candidate that carries nothing is an ordinary candidate.

**Admission (one invocation of Axiom 0, Z₀.execute).** 3a and 3b are unchanged: ω on Cⁿ, then the
criterion of the abstraction on Cⁿ and ω. If it is true, Z₀ judges the carried specifications with
τ_root in order, each on Cⁿ extended by the ones before it, so that an ontology may be bound to a
criterion carried in the same candidate. A carried ontology is bound to the active criterion by Z₀,
as in phase 2. If τ_root refuses one, the candidate is refused (false), and nothing is appended. If
all are admitted, one event is appended: the execution event of the abstraction, whose coordinate
also lists the addresses of the specifications it carries.

**The index.** When it reads an execution event that carries specifications, the index registers
each as an admitted version at that position, exactly as it registers a specification event. The
active version is still the last admitted one, whichever way it came; `lookups` does not change.

**Replay (R2).** Such an event is checked as every execution event (its versions were active, ω
re-derived from Cⁿ and bound is the payload, the criterion is true on replay), and in addition every
carried specification is checked against τ_root, in order, as a specification event is, and the
coordinate must list exactly what the payload carries. Replay judges the carried specifications as
they are recorded, without binding them again, so that an ontology bound to a wrong criterion is
found also by the replay that does not re-derive candidates (`verify --judgments`).

**The set of abstractions.** An abstraction exists for execution when it has an active criterion
and an active ontology in C. The list in `system.json` names the abstractions of the files; those
that appear later through carried specifications are added when they appear (`System.adopt`): to
the agenda and, by workers, a worker is started for each (by the coordinator when the workers run
in its process; elsewhere `python -m ztes work SYSTEM NAME` accepts a name that is not declared,
and its worker waits until its specifications are carried). A specification carried for an
abstraction makes that abstraction due, as a `govern` step does. A KPI profile is recorded for the
abstractions of the system at its first measurement; one adopted after that is not counted by it.

**Races.** Z₀ may append a candidate one position later without computing it again when the event
that took the position is outside its horizon (Lemma 6). An event that carries a specification of
the abstraction counts as inside it, and a candidate that carries specifications is always judged
again, since the versions it continues may have changed.

## 4. Determinism

Whether the moment of a change is the same under every schedule is a property of the system, not of
Z₀. The pattern that keeps Theorem K: the proposing abstraction records a decision at every point
where one is due, also when it changes nothing (an event that carries no specification), and the
abstractions it may change wait for that decision through an ordinary binding, as the searchers of
the VNS examples wait for the incumbent of their round. A change then takes effect at a position
fixed by complete horizons. A proposer that reads the record "as it stands" gives a valid record
whose course depends on the schedule, as the asynchronous forms do.

## 5. What changes in the code

| Where | Change |
|---|---|
| `model/types.py` | the basic type `specification` (JSON object; the API is checked by τ_root) |
| `model/validation.py` | an ontology may declare at most one field of type `{"list": "specification"}` |
| `substrate/z0.py` | in `execute`, after a true criterion: bind carried ontologies, judge the carried specifications with τ_root in order; one event |
| `substrate/events.py` | the coordinate of an execution event may list the addresses of carried specifications |
| `model/view.py` | `Index.add` registers carried specifications as versions |
| `substrate/governance.py` | `carry`: bind the carried ontologies, judge the carried specifications in order (`carried_refusal`), describe them for the coordinate |
| `substrate/replay.py` | τ_root for carried specifications; the coordinate lists exactly what the payload carries |
| `system/resume.py` | a run continued on a record walks carrying events as Z₀ appends them |
| `system/system.py`, `agenda.py`, `workers.py`, `kpi.py`, `__main__.py` | the set of abstractions grows with the record |

Out of scope for the first version: carried specifications for abstractions served over HTTP
(they run in process), and carrying in other places of a candidate than one top-level field.

## 6. Tests

All of the following are in `tests/test_carried.py`. Each part of the mechanism was also removed
or weakened in turn (22 mutations: the index, replay in both modes, Z₀, the agenda, the workers and
the coordinator, the binding, each rule of τ_root, the walk of a continued run, the profile), and
each mutation fails at least one of these tests.

- **Regression.** Every example of ztes-minimal and of oee-heuristic-agents gives a record identical,
  byte for byte, to the baseline (no existing coordinate gains a field), and the same histories by
  workers.
- **New.** A small example in which an abstraction steers others by a rule over the record:
  - a change it proposes is active from its event on, and replays;
  - a carried criterion and the ontology bound to it in one candidate;
  - a refusal by the proposer's criterion, and one by τ_root (a version with a gap, an ontology bound
    to an inactive criterion), each leaving C unchanged;
  - a new abstraction brought in by a candidate is executed by the agenda and by workers;
  - the same histories under random schedules when the decision pattern of §4 is followed;
  - a record whose carried specification was altered fails replay at that event (its body, its
    version, the criterion it is bound to), in both modes;
  - an abstraction that does not read the proposer is evaluated again when its specification is
    carried, by the agenda and by a waiting worker;
  - a carrying candidate is judged again after a lost race;
  - an interrupted run continues to the same record, cut before, at and after a carrying event;
  - the profile, the coordinator and the command line (`run`, `verify`, `explain`).

## 7. Order of work

1. Baseline (done): hashes of the records and times of every example, under the agenda and by
   workers.
2. Optimizations that keep every record identical, one per commit.
3. This proposal (done); then the example of adaptive VNS in oee-heuristic-agents that uses it.
