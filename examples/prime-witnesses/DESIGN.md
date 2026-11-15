# Admitted prime witnesses and stream interactions: design (step 0)

*Paper: §8.3. Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** After `dedekind-cut`: a relation with several valid answers. Which one is admitted depends on what the record holds at that moment (D1), and a finite witness proves nothing universal.

The executable counterpart of §8.3. A prime stream is consumed by two independent interaction
abstractions: Goldbach witnesses for specified even numbers, and pairs of primes at distance two.

## 1. Problem

Certify the primes up to 23. For each of the even numbers 10, 14, 20 admit one representation as a
sum of two certified primes. Admit the pairs of certified primes at distance two, in increasing
order. No universal statement is to be established, only finite witnesses.

## 2. Decomposition into binary relations

    Prime    = { (P, p) : p the least prime greater than max P, p ≤ 23 }      ⊆ 𝒫fin(ℕ) × ℕ
    Goldbach = { ((2m, P), (2m, p, q)) : p + q = 2m, p ≤ q, p, q ∈ P }         ⊆ (ℕ × 𝒫fin(ℕ)) × ℕ³
    Twin     = { ((t, P), (p, p + 2)) : p > t, p, p + 2 ∈ P }                   ⊆ (ℕ × 𝒫fin(ℕ)) × ℕ²

Goldbach and Twin are **multivalued**: 10 = 3 + 7 = 5 + 5, and after (3, 5) both (5, 7) and (11, 13)
are later twin pairs.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `primes` (αP) | Prime | the least k > p with no recorded prime dividing it | p < w ≤ 23, no recorded prime q ≤ √w divides w | `primes` |
| `goldbach` (αΣ) | Goldbach | for the k-th even number E[k]: the pair with the smallest p among the **visible** primes; ⊥ while there is none | w.even = E[k], p + q = even, p ≤ q, both recorded primes | `goldbach`, `primes` |
| `twins` (αΔ) | Twin | the smallest visible p > last p with p + 2 also visible; ⊥ while there is none | q = p + 2, both recorded primes, p > last p | `twins`, `primes` |

## 4. Design decisions and what they illustrate

* **D1: the record resolves a multivalued relation.** The ontology of `goldbach` takes the smallest p
  among the primes visible at the invocation. Which witness is admitted therefore depends on the
  record: for 10 it is 5 + 5, because 7 is not yet certified when 5 is; for 20 it is 3 + 17, because
  by then 13 and 17 are both certified. No choice function is involved.
* **D2.** The criteria check only the arithmetic relation and the prime certificates; they do not
  search.
* **Witness is not proof (§8.3).** Admitted witnesses do not establish that every even number is a
  sum of two primes or that there are infinitely many twin pairs. At the end `twins` is in permanent
  wait because no further pair is visible under the bound 23: a statement about this regime, not
  about the integers.
* **The same question, answered on a complete horizon.** `goldbach/ontology.v2` is not in the plan. It
  is ⊥ until the primes reach E[k] − 2, so every prime that could take part is recorded before a
  pair is proposed, and the pair is then always the one with the smallest p (3 + 7 for 10). Under
  v1 the admitted pair depends on when `goldbach` is invoked, which the agenda fixes and a race
  between workers does not ([docs/distribution.md](../../docs/distribution.md)).
* **Interaction only through C.** `goldbach` and `twins` never call `primes`; they read its lineage
  and are evaluated again whenever it admits a prime.

## 5. Plan

No plan: phase 1, phase 2, phase 3 until terminal.

## 6. Expected end

Primes 2, 3, 5, 7, 11, 13, 17, 19, 23; the candidate 29 is refused, so `primes` is closed.
Goldbach witnesses: 10 = 5 + 5, 14 = 7 + 7, 20 = 3 + 17. Twin pairs: (3, 5), (5, 7), (11, 13),
(17, 19). `goldbach` and `twins` end in permanent wait. The record has 23 events, 26 with the KPI step
at the end, and R2 replays it.

## 7. Files

```
system.json                                   types Goldbach, Twin; constants MAX, E; bindings primes, p, k, last; expect
DESIGN.md
abstractions/{primes, goldbach, twins}/{criterion, ontology}.v1.json
```

## 8. Execution indicators (KPI)

The plan ends with one KPI step. The profile it records:

```
primes:   invoked 10, admitted 9, Not Yet 0, false 1
goldbach: invoked 7,  admitted 3, Not Yet 4, false 0
twins:    invoked 7,  admitted 4, Not Yet 3, false 0
```

`goldbach` and `twins` end at Not Yet when the primes admitted so far give them nothing to propose. The one false judgment closes `primes` at its bound.
