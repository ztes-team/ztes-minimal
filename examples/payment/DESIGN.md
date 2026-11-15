# Identical payments with different admission grounds: design (step 0)

*Paper: §1.1. Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** The example of §1.1 of the paper: two events with the same payload and different grounds, a protective refusal, and evidence that only the record keeps.

The executable counterpart of the example in §1.1. Two payments of 50 from account a to account b
have the same extensional payload but different admission grounds: one is admitted after a
successful fraud check, the other after an authorized override of a failed check. A third
identical payment, with a failed check and no override, is refused.

## 1. Problem

Process three payment requests a → b, 50 each. A request is executed only if its fraud check passed
or a supervisor has authorized an override. A repeated identical request fails the fraud check.
The supervisor authorizes an override for request 2 only.

## 2. Decomposition into binary relations

    Request  = { (k, R[k + 1]) : k < 3 }                                           ⊆ ℕ × Req
    Check    = { (r, (id(r), passed)) : passed ⟺ no earlier identical request }   ⊆ Req × (ℕ × 𝔹)
    Override = { (c, (id(c), by)) : c failed, AUTH(id(c)) = by }                     ⊆ Chk × (ℕ × Text)
    Transfer = { ((r, c, o), (from(r), to(r), amount(r))) : c passed or o exists }   ⊆ (Req × Chk × Ovr) × Pay

The right component of Transfer contains no trace of the ground: two transfers can be equal as
values, U(e) = U(e′), while e ≠ e′.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `requests` | Request | the next request of the list R | consecutive id, amount > 0, from ≠ to | `requests` |
| `fraud_check` | Check | for the next request: passed unless an earlier identical request exists | the same rule, checked against the recorded requests | `requests`, `fraud_check` |
| `override` | Override | for a failed check with an entry in AUTH: {id, by} | id in AUTH, by = AUTH[id], the check is recorded as failed, no earlier override | `fraud_check`, `override` |
| `transfer` | Transfer | for the next request, once its check is recorded: {from, to, amount} | the payload equals the request, **and** the check passed **or** an override is recorded | `requests`, `fraud_check`, `override`, `transfer` |

## 4. Design decisions and what they illustrate

* **D2: proposing is not admitting.** The ontology of `transfer` proposes the transfer as soon as a
  check is recorded, whatever its result. Only the criterion decides, so a failed check without an
  override is a **protective rejection** (τ false), not a missing candidate (§6.2, last paragraph).
* **The ground is evidence in the record, not in the payload (S1.4).** Transfers 1 and 2 have the
  same payload. What distinguishes them is the prefix on which each was judged: a passed check for
  the first, a failed check and an override for the second. R2 reproduces both judgments only
  because these events are retained (Counterexample 4, Table 5).
* **Waiting and re-evaluation.** Transfer 2 is first refused (no override yet); when the override is
  admitted, the agenda evaluates `transfer` again and it is admitted. Transfer 3 is refused and,
  with no override possible, `transfer` stays closed: later requests cannot bypass it.

## 5. Plan

No plan: phase 1, phase 2, phase 3 until terminal.

## 6. Expected end

| Request | Check | Override | Transfer |
|---|---|---|---|
| 1 | passed | – | admitted: {a, b, 50} |
| 2 | failed | supervisor-1 | first refused, then admitted: {a, b, 50} |
| 3 | failed | – | refused (protective rejection) |

`transfer` is closed; `requests`, `fraud_check` and `override` end in permanent wait. The record has
18 events, 21 with the KPI step at the end, and R2 replays it. Judged on the same prefix without the override event, the second
transfer is refused, although its payload is identical to the first: the evidence, not the payload,
carries the ground.

## 7. Files

```
system.json                                   types Request, Check, Override, Payment; constants R, AUTH; shared bindings; expect
DESIGN.md
abstractions/{fraud_check, override, transfer}/abstraction.json   bindings of one abstraction (req, check, …)
abstractions/{requests, fraud_check, override, transfer}/{criterion, ontology}.v1.json
```

## 8. Execution indicators (KPI)

The plan ends with one KPI step. The profile it records:

```
requests:    invoked 4, admitted 3, Not Yet 1, false 0
fraud_check: invoked 4, admitted 3, Not Yet 1, false 0
override:    invoked 3, admitted 1, Not Yet 2, false 0
transfer:    invoked 4, admitted 2, Not Yet 0, false 2
```

The two false judgments of `transfer` are protective refusals. A refusal is not an event, so the record alone does not show how often it happened; the profile does.
