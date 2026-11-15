# Integer factorization with reused admitted certificates: design (step 0)

*Paper: §8.7, Table 7. Tags: [C] epistemic, [ω] ontological, [τ] eschatological (see the README).*

**What this example adds.** After `prime-witnesses`: earlier admitted results are reused as certificates, so search is replaced by checking, and an abstraction waits (Not Yet) for the certificates it needs.

The executable counterpart of §8.7 and Table 7 of the paper. Admitted history and interaction
between abstractions replace repeated search by checking: a new target is factored by reusing the
last admitted factorization certificate and the admitted prime certificates.

## 1. Problem

Factor the targets 2,310, 30,030, 510,510 and 7,429, which arrive one after another, into primes.
Every factor must carry a certificate of primality, and every factorization must be checkable
without repeating the search.

## 2. Decomposition into binary relations

    Prime   = { (P, p) : p is the least prime greater than max P, p ≤ 23 }           ⊆ 𝒫fin(ℕ) × ℕ
    Target  = { (k, T[k]) : k < 4 }                                                 ⊆ ℕ × ℕ
    Factor  = { ((n, h, P), c) : c = (n, F, m, g), ∏F = n, F ⊆ P,
                                 m = n(h), g = gcd(n, m) }                          ⊆ (ℕ × Cert × 𝒫fin(ℕ)) × Cert

P is the set of certified primes so far, T the list of targets, h the last factorization
certificate, n(h) the number it certifies, F the factors with multiplicity, m the reused
certificate, and g the gcd that carries the reuse.

## 3. Lifting: the abstractions

| Abstraction | Relation | [ω] Ontology Sω: what it proposes | [τ] Criterion Sτ: what it admits | [C] Horizon |
|---|---|---|---|---|
| `targets` (αT) | Target | the next target T[k], only when every earlier target is factored (k = number of factor certificates); ⊥ otherwise | w > 1, w not seen before, and k = f | `targets`, `factor` |
| `primes` (αP) | Prime | the least k > p with no recorded prime dividing it (in (p, 2p + 1], by Bertrand) | p < w ≤ 23 and no recorded prime q ≤ √w divides w: a certificate by finite divisibility | `primes` |
| `factor` (αF) | Factor | g = gcd(n, m) with the last certificate (n, …) = h; the factors of g from h; the cofactor n/g by recorded primes only; ⊥ while some factor has no prime certificate yet, or n is already factored | product identity ∏F = n; every factor has a prime certificate; provenance: g = gcd(n, m) and m is the last admitted certificate | `targets`, `primes`, `factor` |

The certificate is a record payload:

```json
{"n": 30030, "factors": [2, 3, 5, 7, 11, 13], "reused": 2310, "gcd": 2310}
```

## 4. Design decisions and what they illustrate

* **No selector (D1).** Many earlier certificates could be reused. The ontology always takes the
  last admitted one (`"select": "last"`), so the record resolves the choice and the realization is
  single-valued (§8.7).
* **Separate criterion (D2).** The ontology searches; the criterion only checks: the product, the
  prime certificates, and the provenance of the reused certificate. It does not repeat the search.
* **Waiting through the horizon.** `factor` is ⊥ while a needed prime is not yet certified, and is
  evaluated again only when `primes` admits a new prime (the variant at the end of §8.7, with the
  substrate's agenda in place of an abeyance abstraction). `targets` waits for `factor` in the same
  way, which makes the targets arrive in sequence.
* **Interaction only through C.** No abstraction calls another; `factor` reads certificates admitted
  for other targets and primes admitted by `primes`.

## 5. Plan

No plan: phase 1, phase 2, phase 3 until terminal. No governed change.

## 6. Expected end

Prime certificates 2, 3, 5, 7, 11, 13, 17, 19, 23 are admitted; the candidate 29 is refused, so
`primes` is **closed**. Four factorization certificates are admitted, as in Table 7:

| Target | Reused | gcd | Certificate |
|---|---|---|---|
| 2,310 | none | 1 | h₁: 2 · 3 · 5 · 7 · 11 |
| 30,030 | h₁ (2,310) | 2,310 | h₂: 2 · 3 · 5 · 7 · 11 · 13 |
| 510,510 | h₂ (30,030) | 30,030 | h₃: 2 · 3 · 5 · 7 · 11 · 13 · 17 |
| 7,429 | h₃ (510,510) | 17 | h₄: 17 · 19 · 23 |

In the paper h₁ and the prime certificates already exist when the first target arrives; here they
are produced in the same run, interleaved by the agenda. After h₄, `targets` has no further target
and `factor` has nothing to factor: both are in **permanent wait**. A new target list would be a
governed change of `targets` (a new ontology version) and would resume execution. The system is
terminal; the record has 24 events of the construction, 27 with the KPI step at the end, and R2 replays it.

Note on R2: the substrate's verifier re-derives each candidate from its prefix and then re-judges it.
That is more than the minimum R2 asks for, which is to reproduce the judgment from the recorded
candidate, prefix, and specifications; the criterion alone already checks h₄ without any search.

## 7. Files

```
system.json                                   type Cert; constants MAX, T; bindings primes, p, prev; expect
DESIGN.md
abstractions/targets/abstraction.json         bindings k, f, seen
abstractions/targets/{criterion, ontology}.v1.json
abstractions/primes/{criterion, ontology}.v1.json
abstractions/factor/{criterion, ontology}.v1.json
abstractions/factor/ontology.v1.py           the body of the ontology, as a Python function
```

## 8. Execution indicators (KPI)

The plan ends with one KPI step. The profile it records:

```
targets: invoked 9,  admitted 4, Not Yet 5, false 0
primes:  invoked 10, admitted 9, Not Yet 0, false 1
factor:  invoked 10, admitted 4, Not Yet 6, false 0
```

`factor` is at Not Yet six times and `targets` five times: each waits for events of the other lineages. Waiting costs an invocation and leaves no event.
