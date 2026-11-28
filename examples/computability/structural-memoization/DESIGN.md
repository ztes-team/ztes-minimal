# Derivational analogy and structural memoization in supply disputes

This model asks whether solving one dispute can save search in a different dispute while preserving the causal origin and local admission of each payment. A transport-damage case produces a settlement plan. A cold-chain case reads the plan through its declared horizon, binds it to different evidence and parties, and proposes its own settlement. A contractual exclusion tests whether the local criterion can still refuse exactly the same candidate. The model compares the avoided work with the cost of publishing and checking the plan. [Observed results](results/RESULTS.md)

## 1. What is reused

| Concept | Meaning in this example |
|---|---|
| Event identity and reuse | An admitted occurrence has an immutable coordinate and payload. A later invocation with access to it can reuse its recorded content. Two occurrences can carry equal amounts or even identical payloads and still have distinct origins. |
| Derivational analogy | Two admitted diagnoses from distinct abstractions reduce to the same structural problem in a specified common abstraction. This gives the target ontology a reason to try a particular derivation. |
| Structural memoization | Building a parameterized plan is itself a subcomputation. The first case records its result. A compatible target reads the same published object and skips construction of that plan. Its evidence, arithmetic, permissions and final admission are evaluated locally. |

**Analogy through a common ancestor enables structural memoization.** The common ancestor is the executable funding abstraction $\mathcal B$ in the specialization hierarchy. When two admitted diagnoses reduce to the same signature in $\mathcal B$ and the construction versions agree, the target can reuse the plan graph built in the source case. This saves the search that produced the graph. Under S1, the target’s active criterion judges each completed candidate against its own prefix, and Axiom 0 admits the step when that judgment is positive. R1 requires any change of governing rules to be admitted under the authority already in force. R2 makes each recorded admission independently verifiable under its original prefix and versions. In the exclusion case, the ontology can therefore retrieve the very same plan while the target criterion still refuses payment.

In the literature, reusing justified parts of a previous solution process is called *derivational analogy*, within case-based reasoning. Its use to reduce subsequent problem-solving effort is a form of *speedup learning*. The OEE question is how an admitted derivation becomes an input to another ontology and how the target's admission can be verified from its own prefix. [Veloso and Carbonell, 1993](https://doi.org/10.1023/A:1022686910523) · [Veloso, 1994](https://link.springer.com/book/10.1007/3-540-58811-6)

## 2. Two diagnoses and one shared structural problem

Use two case lineages in one append-only record $C$. The source abstraction $A_T$ recognizes transport damage from an inspection attributed to the designated inspector and a carrier's delivery report. The target abstraction $A_C$ recognizes a cold-chain breach from a lot-linked temperature observation, a calibration record and a quality determination. A clean delivery report and an adverse inspection may both be admitted. The transport criterion specifies which evidence establishes damage. Issuer names in this fixture represent synthetic attestations. Where order affects a judgment, the deciding observation or merge must be recorded. Record position expresses prefix dependence.

| Case | Admitted obligation $D$ | Primary limit $S$ | Nominated guarantee limit $G$ | Expected settlement |
|---|---:|---:|---:|---|
| A · Transport damage | 90 | 60 | 40 | Primary pays 60 and guarantor pays 30. A publishes the derived plan. |
| B · Cold-chain breach | 65 | 45 | 30 | Primary pays 45 and guarantor pays 20 after local confirmation of coverage. |
| B′ · Cold-chain breach with exclusion | 65 | 45 | 30 | The same plan is found. The local policy excludes this cause. The proposed settlement produces no payment entry. |

Amounts are integer units of the same settlement asset within each case. Each fixture names a primary payer, a nominated guarantor and a beneficiary. The primary-first rule exhausts available primary cover before any guarantee draw. Each positive fixture supplies the requisite authorization and available funds.

### The common ancestor in the specialization hierarchy

Following OEE §5.4, Definition 12, define a lower-ranked executable abstraction $\mathcal B$. Its ontology reads a declared obligation summary, two funding roles, their limits, and the primary-first rule. Its criterion accepts well-formed summaries with documented inputs, compatible units and nonnegative amounts. Its output describes the funding structure. The two higher diagnostic abstractions consume an admitted base summary and additionally require their respective evidence. Compare their requirements on the same case inputs. Every successful higher diagnosis cites an admitted base event. A funding-only run supplies a witness for each strict refinement: the base summary is admitted while the specialized invocation awaits its evidence. Rank here refers to criterion specialization as in Appendix A.1. The pattern is recorded as ordinary event content on the epistemic axis.

Define $q_T$ and $q_C$ on already admitted diagnoses with the required fields. Each projects its local funding roles onto the ordered roles *primary* and *supplemental*, normalizes the settlement unit to a typed parameter, and maps amounts to a declared comparison class. For the fixtures the output is the tuple

```text
(funding-interface-v1, recognized obligation, primary first,
 nominated supplemental instrument, compatible units,
 0 < primary limit < obligation <= primary limit + supplemental limit)
```

The comparison relation is exact equality of these tuples. Thus $q_T(e_A)=q_C(e_B)=q_C(e_{B′})$ while the occurrences retain their own coordinates. A and B instantiate the cross-abstraction analogy. B and B′ are two fixtures for the same target abstraction. The signature records the existence of a nominated instrument. The target's coverage decision remains open at diagnosis. This makes recognition useful *before* a settlement has been found.

### A categorical specification of the comparison

Write $P$ for the set of canonical signatures and $D_T,D_C$ for admitted transport and cold-chain diagnoses on which the reductions are defined. In **Set**, the pullback $D_T\times_P D_C$ consists of the pairs $(e,f)$ satisfying $q_T(e)=q_C(f)$. Each pair retains two distinct occurrences. The implementation realizes this comparison by exact tuple equality. Its reusable output is a graph of typed operations with ordered input ports. One can also describe that graph coalgebraically by assigning each node its label and ordered list of dependencies. The funding limits, coverage decision and authority of the target enter when the graph is bound and judged.

An empty execution prefix and an empty state carrier play different roles. A coalgebra $c:X\to F(X)$ on $X=\varnothing$ has no state at which to evaluate $c$. The empty prefix $\varepsilon$ is an element of the record carrier $E^*$. A pointed coalgebra can designate $\varepsilon$ and describe its transitions once a dynamics has been specified. In ZTES, initialization supplies the root authority, the ontology realizes a candidate on a given prefix, and Axiom 0 governs its admission there. The pullback specifies the exact comparison used in finding the graph. The operational rules explain how the graph becomes available and whether a particular application enters the record. [Rutten, *Universal coalgebra: a theory of systems*](https://ir.cwi.nl/pub/48) · [Pointed coalgebras and initial states](https://arxiv.org/abs/1305.0576)

## 3. How the first case earns a reusable plan

Start A with an empty pattern catalogue. Supply a finite library of typed primitives for allocating from a named source up to a limit, computing the remaining obligation and assembling a balanced settlement. The library also permits single-source attempts and either source order. Generate candidate compositions in increasing size, breaking ties by a fixed order of primitives and roles. Bound enumeration to one allocation per source, one residual per allocation and one closing operation. Each operation must have its inputs available from the interface or an earlier operation. The planner selects the first graph satisfying full coverage, source limits and primary priority for the signature.

The planner constructs the graph from the signature. Its search order, primitive meanings and validity checks are versioned. Concrete evidence identifiers and amounts enter when the graph is instantiated. For A, the expected graph allocates from the primary source, computes the residual, allocates the residual to the guarantor and credits the beneficiary with the sum. A primary-only attempt leaves 30 uncovered. Drawing the full guarantee first would give 40 from the guarantor and 50 from the primary, violating primary priority. The search trace must expose the candidates actually examined and the selected graph.

Before publication, the catalogue criterion checks the graph's typed dependencies and its conditional justification. Write $x=\min(D,S)$ and $y=D-x$. Under the signature's inequalities, $x=S$, $0<y\le G$ and $x+y=D$. A typed graph checker can propagate these relations through the finite primitive library. The graph also carries obligations to verify the applicable guarantee, available balances and beneficiary at the target. This justification applies to every binding in its stated range. A's successful payment alone would establish only one instance.

| Stored with the published pattern | Bound or checked by the target |
|---|---|
| Unique pattern reference, source diagnosis and successful derivation references | Target case, diagnosis, evidence and active contract |
| Canonical signature and compatible interface, reduction, planner, primitive and checker versions | Current compatibility and availability through the declared horizon |
| Typed graph, role parameters, preconditions and conservation justification | Actual parties, units, amounts, caps, coverage and settlement authority |

A checker may revalidate the short graph and its justification without enumerating competing plans. This difference is what the experiment measures. General discovery of $\mathcal B$, the reductions or a valid plan language from a single successful case is outside this design.

## 4. Endogenous use in the target

1. **Admit and publish.** A records its diagnosis, selected derivation and authorized settlement. A catalogue abstraction reads these admitted events, verifies their association and publishes the parameterized graph as an execution event. The publication is produced by these specifications during execution.
2. **Declare what the target can see.** B's ontology reads its diagnosis and an admitted catalogue snapshot through named bindings. The snapshot names the publications available at that cut, including the empty list when applicable. The catalogue validates each reference against its own admitted lineage. This makes visibility explicit even when publication and target execution can interleave.
3. **Select and instantiate.** Check the signature and construction versions. Among compatible publications use the first by catalogue publication ordinal. If a graph fails a local guard, try the remaining compatible graphs in that order, then resume ordinary search over untried plans. These choices belong to the versioned ontology. A bound invocation on a fixed prefix and inputs has at most one completed candidate.
4. **Judge locally.** B's settlement criterion independently checks the target evidence, guarantee scope, balances, beneficiary, conservation, and absence of a prior settlement on the designated settlement lineage for this obligation. Post the two allocations as one settlement entry. It identifies the target evidence and the origin of its plan, either the local derivation for a fresh search or the selected publication for reuse. A duplicate invocation cannot pay the obligation twice. In B′ the exclusion prevents payment. If an observable reason is needed, a diagnosis abstraction may admit a separate event recording the exclusion and the failed applicability check.

The published object has one occurrence in the common OEE space. Its address locates it and its payload contains the graph. In the reference implementation, ordinary `from` bindings expose execution payloads. Use a unique domain reference such as *(catalogue lineage, publication ordinal)* in the payload, enforce uniqueness at admission, and let the audit resolve it to the actual occurrence. Treat source derivation references the same way. The target references the existing publication. Its application receives a fresh coordinate. Pattern publication and application are data operations under the active rules. [ZTES context bindings](https://github.com/ztes-team/ztes-minimal/blob/d49981a3c42a644299d45180afbc2ff87e77c2b1/docs/writing-a-system.md#L174-L195)

For example, a reader starting at B's payment of 45 + 20 should be able to follow two independent references. One leads through the pattern publication to the graph constructed in A. The other leads through B's coverage decision to the policy version, quality determination and calibrated observation for B's lot. Together they answer two different questions about the payment, namely who supplied the plan and what justified using it here.

## 5. Experiment and acceptance criteria

Run B from the same local facts and governing versions twice. Use the same implementations, target invocation order and binding declarations. In the **cold** run B receives the valid empty snapshot taken before A's publication. In the **warm** run B receives a snapshot containing the publication. The identity of the snapshot is recorded in each run. The driver supplies fixture observations and schedules invocations. Pattern construction, publication, selection and admission all run inside the specified abstractions.

| Run | Evidence required for acceptance |
|---|---|
| A, construction | The initial catalogue is empty. An admitted, locally successful derivation supports a new publication. Its graph, justification and version dependencies can be recovered. |
| B, cold | Fresh search finds a 45 + 20 settlement. Report the graphs examined and the local checks performed. |
| B, warm | The target references A's exact publication, admits the same local allocation and constructs or examines fewer fresh graphs than cold B. Compare beneficiary, amounts and obligations covered. Each run retains its own coordinates. |
| B′, exclusion | The target sees the same publication and recognizes the same signature. The exclusion is visible to its own criterion. Even a directly submitted candidate with the proposed 45 + 20 split must fail that judgment. No settlement for that proposal is admitted. |
| Incompatible version or unavailable publication | A version mismatch or a snapshot without the referenced publication leaves the ordinary search path available. A candidate claiming a dangling or invisible reference fails the applicable reference check. |

Count fresh search expansions, completed candidate graphs tested, publications inspected, graph checks, bindings and local judgments. Use the same counting boundaries in both target runs. Report A's search and publication cost separately, and report full replay cost separately. Fewer fresh expansions establish avoided search on the fixture. An end-to-end speedup additionally requires lookup, binding and validation to cost less than the work saved. Report a neutral or negative result if the small fixture does not amortize those costs.

For every run, perform full ZTES replay from its start. Full replay re-derives internally generated candidates and checks recorded admissions under their original prefixes and versions. A bound external observation is checked as recorded. For a fault test, alter the pattern reference on an otherwise valid recorded target application and require full replay to reject the altered derivation. A rejected candidate or pending invocation ordinarily appends no event. The experiment report must distinguish observed attempts from admitted events. The target's use of an old graph to propose a new event and R2's replay of an existing record answer different questions. [ZTES full replay](https://github.com/ztes-team/ztes-minimal/blob/d49981a3c42a644299d45180afbc2ff87e77c2b1/ztes/substrate/replay.py#L44-L98)

## 6. Extension with governance, obstruction and compensation

Run this extension after the plan-reuse comparison so its cost and effects can be reported independently. Keep a persistent goal $H$ of crediting the beneficiary the full admitted obligation $D$.

- **Waiting and obstruction.** A missing inspection may leave an invocation pending. To classify $H$ as *Not Yet*, exhibit a permitted continuation that reaches it. For the *False* fixture, the assessed obligation and the primary cap are fixed at $D>S$. The credit rule in $r_1$ permits only primary draws, even if a funded guarantee is observed. All continuations under the fixed rule preserve the bound of $S$ on cumulative credit. These conditions define a successor-closed obstruction certificate for $H$. Failure of one proposed plan establishes only that attempt's outcome.
- **R1.** Provide an authority in the prior regime able to admit a governance event introducing risk-sharing. Its payload carries the new specification under the repository's standard activation rules. The new regime permits a guarantee draw against its own recorded authorization and funds, making the same $H$ reachable. Bind governance to the affected case abstraction so the source transition cannot silently change the target's baseline. [ZTES specification activation](https://github.com/ztes-team/ztes-minimal/blob/d49981a3c42a644299d45180afbc2ff87e77c2b1/docs/writing-a-system.md#L399-L446)
- **R1-c.** Give the changed obligation a prior recorded consequence, such as an administrative fee already debited from a supplier. For the admitted governance trigger $d$ and its preceding prefix $C$, derive the affected set $\mathrm{Aff}(d,C)$ from the declared scope and recorded dependencies. Reconstruct each affected actor's relevant prior horizon. Append a correction linked to the original debit, and require a coverage witness recording the required corrective outcomes for each affected actor before admitting compensation closure. An authorized finding of non-compensability can document coverage where the rules allow it. Full payment of $D$ has its own settlement condition. In the negative fixture, omit one actor's witness and attempt closure. The closure criterion must reject it, even though the shorter prefix itself can replay successfully.

The OEE manuscript discusses horizons and analogy in §§5.1 and 5.4, measured reuse in §8.8, and compensation coverage in §9.3. The supplementary experiment supplies the concrete search language, reductions, local contracts and observations used here. [Run the experiment](README.md) · [Read the results and provenance checks](results/RESULTS.md)
