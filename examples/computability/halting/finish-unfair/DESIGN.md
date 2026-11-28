# tick / finish with a scheduler that never chooses finish: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md), and the abstractions in [`../finish-fair/DESIGN.md`](../finish-fair/DESIGN.md). Base paper: §6.2, Theorem 4, §5.2. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** A goal that is reachable at every prefix and never taken, class 𝔚.
`tick` and `finish` are those of `finish-fair`. `policy` is a boundary abstraction whose source,
`{"seed": 1, "size": 1, "below": 1}`, always gives 0: a scheduler that never chooses finish.

## 1. What every prefix shows

`policy` is a boundary abstraction (§5.2): its candidate is an occurrence, and its criterion admits
1 as well as 0. At every prefix a decision for finish is therefore admissible, and after an even
number of recorded ticks finish follows it. The goal is reachable, so its status is Not Yet
(Definition 6), at every prefix.

The scheduler never takes that branch. An unbounded run of this kind establishes the goal at no
prefix and has no False prefix: class 𝔚 of Theorem 4.

**What is fixed.** The regime is the recorded specifications. The criterion of `policy` names both
choices, 0 and 1, and its boundary ontology takes either as an occurrence. The source
`{"seed": 1, "size": 1, "below": 1}` is the environment of this run, one observed path of zeros
among the executions of the regime; it is not a specification and is not recorded
(`ztes/system/sources.py`). A regime that could only give 0 would make finish unreachable at every
prefix, class 𝔓: that is `finish-unreachable`.

## 2. Plan and expected end

```
phase 1, phase 2   policy, tick and finish v1
phase 3            a window of 40 admissions
kpi                execution indicators (the profile), once, at the end
```

20 decisions and 20 ticks under the agenda, and no finish: 50 events. The run is paused, not
terminal. Under workers the 40 admissions may divide differently between `policy` and `tick`. R2
replays the record.

Its execution payloads, decisions and ticks, are those of
[`finish-unreachable`](../finish-unreachable/DESIGN.md); the recorded specification of `policy`
differs, and so does the class. `tests/test_halting.py` checks both at every prefix of the window.
The claim for every prefix of the unbounded run rests on the specifications: the boundary `policy`
admits a decision for finish whenever finish is not recorded.

## 3. Files

As in `finish-fair`, with a source in `system.json` and a boundary ontology for `policy`:
`system.json`, `lib.py`, `DESIGN.md` and `abstractions/{policy, tick, finish}`.
