# Structural memoization under governed change: one thread

*Not an example of the paper. This extends the co-authors' model in the parent directory and leaves
its experiment, its timing series and its archived records unchanged. Base paper: §5.4 and
Definition 12, Proposition 14, D1/D2, R1, R2, Corollary 9, §6.5, §9.3. Tags: [C] epistemic, [ω]
ontological, [τ] eschatological.*

**The thread.** One record holds the whole sequence:
1. a plan is derived and published;
2. it is reused where the signature matches and the case declares its source as a precedent;
3. a case comes that the rules cannot settle;
4. the review board decides, and the rules are changed under prior authority;
5. an earlier pattern is checked again under the new versions, or a plan is derived, and the
   results are reused again;
6. the compensation is paid, and the case is closed.

Reuse and governance share their abstractions and their record. Every claim below is a count or a
judgment in the record, and each has a test (§7).

**The question.** A reviewer of any memoization scheme asks: *what happens to a stored result when
the rules change?* Here a published pattern carries the versions under which it was derived. A
governed change is an admitted event (R1). A pattern crosses it only by an admitted proof under the
new versions. For each admission, R2 shows which pattern it used and which versions judged it.

## 1. What stays from the model in the parent directory

* **The domain:** supply disputes. The diagnoses are `transport` (a damaged inspection) and
  `cold_chain` (a temperature breach and a quality breach). They share the lower-ranked abstraction
  `funding` (§5.4, Definition 12), and the analogy is exact equality of reduced signatures.
* **The plan language:** typed operations `allocate`, `residual` and `credit`; a breadth-first
  search; a symbolic checker that proves a graph for the whole region of its signature, not for one
  binding.
* **The rest:** the catalogue, the snapshot, and local binding and judgment under the target's own
  policy. The driver `experiment.py` keeps the timed cold/warm comparison.

## 2. Tiers, regions, and two planners

* **Tiers.** A case owes D and has ordered tiers of payment with limits L₁ … Lₙ: primary,
  guarantor, reserve, and so on. The rules in force let the first K tiers pay, each only after the
  tier before it is exhausted.
* **Reduced signature:** the number of usable tiers k = min(K, n), and the region j:

      L₁ + … + L_{j−1} < D ≤ L₁ + … + L_j      (j = 1 … k)

  A case above L₁ + … + L_k has no signature and no plan.
* **Plans.** A plan of the language is fixed by the order in which it draws on the tiers. The plan
  for region j draws on 1 … j in order.
* **The checker** works with forms in k + 1 nonnegative parameters: L₁ … L_{j−1},
  r = D − (L₁ + … + L_{j−1}), h = L_j − r, and L_{j+1} … L_k. It refuses a plan for one of these
  reasons:
  * `priority`: a tier is drawn before the tiers above it are exhausted;
  * `undecided`: the region does not decide a comparison;
  * `negative`: a balance can become negative;
  * `short`: the credit is not D.

  The priority is checked at every draw. A check only at the credit, as with two tiers, would admit
  a plan that draws the guarantor before the primary payer once there are three tiers.
* **The planner** is a constant of the plan specifications and part of the versions of a pattern.
  * `breadth-first:v1` extends every plan. It does not know the priority rule, which is only in the
    checker, and so in the criterion. A governed change of the rules therefore needs no new
    planner. The cost of this separation of proposal and admission (D1/D2) is a search that
    tests Σ_{m=1}^{k} k!/(k−m)! plans for region k. Reuse recovers it.
  * `breadth-first-pruned:v1` extends a plan only if the checker refused it as short: a refusal for
    priority, undecided or negative holds for every extension. It tests k(k+1)/2 plans.
* **What the criterion checks.** The plan criterion repeats the search for a derived plan and
  requires the recorded trace and counts. The counts are therefore admitted, not reported.

## 3. Three origins of a plan, and the declared cut

A plan of a case has one of three origins:
* `reuse`: a visible publication of its signature and versions; one proof and one binding.
* `revalidated`: a visible publication of its signature derived under other versions, proved again
  under the versions in force; one proof and one binding.
* `fresh`: the search.

The catalogue publishes a derived or revalidated plan once it is settled. It keeps one pattern per
signature and versions, so a plan whose kind is already listed is not published again.

**The declared cut.** The policy of a case, its local authority, lists the earlier cases it accepts
as precedents. Its snapshot shows only their publications. What a case may reuse is fixed by this
declaration, not by the moment it arrives. The control case D accepts no precedent. It derives
its plan although P₁ exists, and the catalogue does not list a second pattern of that kind. This is
the cold control of the parent experiment, without timing.

## 4. Systems

All four share `lib.py` and every specification file except the KPI of `governed` (a test checks
the copies).

| System | K | Planner | Cases | What it shows |
|---|---|---|---|---|
| `regions` | 2 | blind | A, B (region 2); C, E (region 1); D (region 2, no precedent); X (above the bound) | reuse only within a region and a cut; X waits without a plan |
| `scaling` | 5 | blind | Sₖ, Tₖ for k = 2 … 5, each in region k | the work of a fresh derivation grows with k; reuse does none |
| `scaling-pruned` | 5 | pruned | the same | the work of derivation is that of the planner; reuse costs the same |
| `governed` | 2, then 3 | blind | the series of `regions`, then F, G (region 2) and H (region 3) | §5 and §6 in one record |

**The fixtures are declared, the judgments are not.** The observations are constants of the
system: FUNDINGS, POLICIES, EVIDENCE, FEES and DECISIONS. The ontologies of `funding`, `policy`,
`evidence`, `fee` and `board` propose them in order. Their criteria judge the form of each
observation and do not read the tables.

**The same history under every schedule.**
* Cases are taken in the order of their fundings.
* A snapshot waits until every earlier case is done: settled, and published or already listed if
  its plan was derived or revalidated.
* The mandate waits until the fees of its case are debited.

The history of every abstraction, with the criterion and ontology versions that judged each
admission, is then the same under the agenda and under workers. Only the interleaving of the
lineages differs, and concurrent cases are left to the parent experiment.

## 5. Obstruction, decision, governed change, reuse across it (`governed`)

**Obstruction (Proposition 14).** X owes 110 with limits 60, 40 and 50. Under the rules r₁ (K = 2)
its bound is 100. When X reaches planning, `certificate` admits
`{"case": "X", "rules": "r1", "bound": 100, "loss": 110}`. The settle criterion of r₁ credits at
most the first K limits, and the funding of a case is recorded once. Full payment, the persistent
goal H, is therefore unreachable at every prefix of every continuation of r₁.

**Decision.** `board` records the decisions of the review board, the authority that the contract of
the case names. Its criterion admits a decision only from that authority, only on a recorded
certificate, and once per case. A decision by a party of the case, such as `carrier/X`, is refused.

**Governed change (R1, Corollary 9).** `mandate` carries the change. Once the board has decided and
the fees of X are debited, it proposes the rules r₂. The event carries `plan`, `settle` and
`certificate` v2: the bodies of v1 with K = 3, so the reserve tier may pay. The mandate criterion
is the criterion in force. It admits one change, and only when these hold:
* the record holds the certificate;
* the record holds the board's decision;
* the change carries exactly those six specifications, with the same k > K;
* k tiers can pay the certified loss.

Three things are kept apart in the record: who decides (the board), what authorizes (the mandate
criterion of r₁), and what changes (the carried specifications). The rules change, not the facts:
the reserve limit was recorded with the funding.

**Reuse across the change.** P₁ and P₂ carry the versions of r₁. Under r₂:

| Case | Signature (k, j) | Plan | Proofs | Publication |
|---|---|---|---:|---|
| X | 3, 3 | derived: no pattern of that signature | 15 | P₃ (r₂) |
| F | 2, 2 | revalidates P₁: the same graph, proved again under r₂ | 1 | P₄ (r₂, revalidates P₁) |
| G | 2, 2 | reuses P₄ | 1 | |
| H | 3, 3 | reuses P₃ | 1 | |

The plans of A … E are judged by plan criterion v1, and those of X, F, G and H by v2, which the
mandate carried. A candidate for G that cites P₁ as a reuse is refused, whichever versions it
claims. X is settled 60 + 40 + 10: H is reached along the governed history (Corollary 9).

This change only adds a tier. It invalidates no proof of r₁, and the revalidation of P₁ succeeds.
A restrictive change would refuse it, and F would derive its plan again.

## 6. Compensation and closure (§6.5, §9.3)

While X is unsettled under r₁, three fees are debited: 4 and 2 from `carrier/X`, and 3 from
`buyer/X`. The fee criterion admits fees only before a mandate of the case, so the affected set
follows from the record. Each refund links an affected party to its debits:
* `buyer/X`: 3, for `fee/2`;
* `carrier/X`: 6, for `fee/1` and `fee/3`.

The closure criterion admits closure only when every affected party is refunded, for the sum of
the debits (9).

## 7. Claims and their tests

All tests are in `tests/test_structural_memoization_thread.py`.

| Claim | Test |
|---|---|
| A reused plan costs one proof in the ontology and one in the criterion, whatever k and the planner | `test_a_reused_plan_costs_one_proof_in_the_ontology_and_one_in_the_criterion` |
| The work of a fresh derivation is that of the planner version: 4, 15, 64, 325 (blind) or 3, 6, 10, 15 (pruned) | `test_the_work_of_a_fresh_derivation_is_that_of_the_planner_version` |
| These counts are admitted: a shorter trace or a smaller count is refused | `test_the_trace_of_a_derived_plan_is_judged_so_its_counts_are_admitted` |
| Reuse happens only within the region of the signature (Definition 12) | `test_reuse_happens_only_within_the_region_of_the_signature` |
| What a case may reuse is fixed by its declared cut | `test_what_a_case_may_reuse_is_fixed_by_its_declared_cut` |
| A case above the bound of the rules has no plan | `test_a_case_above_the_bound_has_no_plan_under_the_rules` |
| The bound of the certificate is the bound of the settle criterion (Proposition 14) | `test_the_certificate_bound_is_the_bound_of_the_settle_criterion` |
| Only the authority named in the contract decides, and only on a certificate | `test_only_the_authority_named_in_the_contract_decides_and_only_on_a_certificate` |
| The mandate needs a certificate, a decision, and enough tiers; it carries exactly six specifications (R1) | `test_the_mandate_needs_a_certificate_a_decision_and_enough_tiers` |
| The rules change once; the certified case is paid in full under the new ones (Corollary 9) | `test_the_rules_change_once_and_the_certified_case_is_paid_in_full_under_the_new_rules` |
| A pattern of the earlier rules crosses the change only by a new proof | `test_a_pattern_of_the_earlier_rules_crosses_the_change_only_by_a_new_proof` |
| A revalidation of another signature, or of a graph the checker refuses, is refused | `test_a_revalidation_is_refused_for_another_signature_or_a_graph_the_checker_refuses` |
| Closure needs a refund for every affected party (§9.3) | `test_closure_needs_a_refund_for_every_affected_party` |
| Every abstraction has the history of the agenda under workers | `test_every_abstraction_has_the_history_of_the_agenda_under_workers` |

## 8. Results

**`scaling` and `scaling-pruned`.** Every target reuses the plan of its source.

| k | Plans tested, blind | Plans tested, pruned | Proofs of a reuse (ontology / criterion) |
|---:|---:|---:|---:|
| 2 | 4 | 3 | 1 / 1 |
| 3 | 15 | 6 | 1 / 1 |
| 4 | 64 | 10 | 1 / 1 |
| 5 | 325 | 15 | 1 / 1 |

A derived plan costs as many proofs in its ontology as it tests, and one more in its criterion.

**`regions`.**
* B reuses P₁ (region 2) and E reuses P₂ (region 1).
* D derives its plan in 4 tests: P₁ exists, but it is not in D's cut.
* X has a snapshot and no plan.

**`governed`.**
* 118 events. The KPI is the table of §5, the certificate of X, fees 9, refunds 9, and closure of X.
* Plans tested over the nine planned cases: 25, plus one revalidation. Without a catalogue they
  would test 54.

**Records.** 70, 89, 89 and 118 events. Each record is pinned in `tests/test_records.py`. Each is the
same under workers, abstraction by abstraction. Each system runs in under a second.

## 9. What these counts depend on

* **The planner.** A derivation costs what the planner version makes it cost. A reuse costs one
  proof in the ontology and one in the criterion, under either planner and for every k.
* **The catalogue.** Retrieval is a linear scan of the declared cut (`inspected`), and its cost
  grows with the cut.
* **The change.** The change here is permissive, so every revalidation succeeds.

## 10. Not in this step

* A restrictive change, under which a revalidation is refused.
* Memoization of the refund plan across cases with the same affected-set signature.
* Concurrent cases with different cuts. That is the timed cold/warm comparison of the parent
  experiment.
* Discovery of the common abstraction from cases.
* A catalogue large enough that retrieval dominates.
