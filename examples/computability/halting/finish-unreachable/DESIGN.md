# tick / finish with a deterministic scheduler that never proposes finish: design (step 0)

*Not an example of the paper; the model is described in [`../DESIGN.md`](../DESIGN.md), and the abstractions in [`../finish-fair/DESIGN.md`](../finish-fair/DESIGN.md). Base paper: §6.2, Theorem 4, Proposition 14. Tags: [C] epistemic, [ω] ontological, [τ] eschatological.*

**What this example adds.** A goal that is unreachable at every prefix, class 𝔓, with a record
whose execution payloads are exactly those of `finish-unfair` (𝔚); the recorded specification of
`policy` differs. Only one specification differs: `policy`
is an ordinary abstraction whose ontology always proposes 0.

## 1. What every prefix shows

The candidate of `policy` is computed, and it is always 0. No prefix has a realization of a decision
for finish, so `finish` is never due. Its criterion would admit finish after an even number of
ticks, but no candidate for it ever arises. The goal is unreachable, so its status is False
(Definition 6), at every prefix.

**The obstacle is in the proposal.** The criteria are those of `finish-unfair`: `policy` would admit
a decision for finish, and `finish` would admit finish after an even number of ticks. Only the
ontology of `policy` differs, and it never proposes 1. Reachability depends on what can be proposed
(D1) as well as on what would be admitted (D2), which is why the two are separate.

The certificate is an inductive invariant in the sense of Proposition 14: "every recorded decision
is 0 and finish is not recorded". It holds at the first prefix, every admitted step keeps it, and it
excludes the goal.

## 2. Plan and expected end

```
phase 1, phase 2   policy, tick and finish v1
phase 3            a window of 40 admissions
kpi                execution indicators (the profile), once, at the end
```

20 decisions and 20 ticks under the agenda, and no finish: 50 events, the payloads of
`finish-unfair` one for one. R2 replays the record.

The class is a property of the regime, the specifications of `policy`, not of the events recorded.
`finish-unfair` and `finish-unreachable` are the smallest pair that shows it.

## 3. Files

As in `finish-unfair`, with `abstractions/policy/ontology.v1.json` an ordinary ontology
(`"result": "[0] if finishes == 0 else None"`) and no source.
