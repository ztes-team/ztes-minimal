# Tracking an admitted search pattern in integer factorization

This experiment extends the certificate-reuse example in §8.7, Table 7, with a governed change of search policy. Its primary question is whether a reader can follow one accepted factorization back to the source observations that changed how the target was searched. Its numerical question is how much work the change saves, including on targets where the pattern has no use. The source and its targets are coprime so that an exact factor of the source cannot solve any target. The reusable object is a checked table of allowed residues.

## What the source discovers

For an odd semiprime $r$, Fermat search tests whether $a^2-r=b^2$ and returns the nontrivial pair $(a-b,a+b)$. The baseline starts at the first parity-compatible integer at or above the square root. It tests odd centers when $r$ has remainder 1 modulo 4 and even centers when the remainder is 3.

On the source 1121 = 19 × 59, the baseline tests 35, 37 and 39. The first two differences, 104 and 248, are nonsquares. The third is 400. The proposed discovery rule tests the fixed vocabulary of moduli 4, 8 and 16, in that order. For each modulus $m$, it constructs the set of center residues for which $a^2-r$ can be a square modulo $m$. It proposes the first mask that would have excluded at least two distinct failed source probes. Moduli 4 and 8 exclude neither. Modulus 16 excludes both. For remainder 1 modulo 16, the permitted center residues are `{1,7,9,15}` modulo 16.

The source observations motivate the proposal. Exhaustive checking over the finite residue classes certifies it for every target with the same remainder. The choice of candidate moduli, their order and the threshold of two failures are part of the supplied discovery policy. The run determines the selected modulus, the mask, its source evidence and the decision to activate it. A target obtains its signature from its input remainder before its factors are known.

The paired activation control holds the source fixed and varies whether the driver invokes the governing change. A second control holds the scheduled discovery and activation calls fixed and substitutes 1457 = 31 × 47 for 1121. Both sources have remainder 1 modulo 16. On 1457 the first eligible center succeeds, so the diagnosis has no failed probes to cite. The expected observations are zero new admissions from the three calls and six probes under the original ontology for the ensuing target 2929. Because only the source can be diagnosed, the same three calls also admit nothing at the end of the record, after the target's failed probes. The experiment reports the call outcomes separately from the admitted record.

## Evidence required from a native ZTES run

| Admitted record | What its reader must be able to recover |
|---|---|
| Source search observations | Source address, active search version, tested centers and square-test outcomes. Record the completed probe block as an observation. An invocation returning Pending contributes no failure event. |
| Diagnosis | Reference to the source probe block, the two distinct failed centers and the threshold they meet. Only the source, the first factored input, can be diagnosed; the failed probes of a later target cannot motivate a pattern. Repeated invocations over the same evidence cannot count as additional failures. |
| Pattern publication | Diagnosis address, modulus, input residue, complete mask and derivation-policy version. The publication criterion independently tests all center residues against the possible square residues. |
| Governing change | Diagnosis and publication addresses, prior active authority and proposed ontology version. The prior authority judges the change under R1. Admission activates the new search policy for subsequent invocations. |
| Target search plan and observations | Target address, input-derived signature, active ontology and either the compatible publication address or the reason for fallback. Record the centers actually tested. A plan that applies the wrong signature must be refused. |
| Target factor certificate | Target and search-evidence addresses, factors, primality evidence and the active factor-criterion address. The same factor criterion checks product and primality under both search versions. The new experiment supplies this criterion at initialization. |

Starting from the factor certificate for 2929, the audit should recover its tested centers, the active search version, the admission that activated it, the published mask and the source probes at 35 and 37. The source and target keep distinct event addresses. On 1643 the audit should instead recover the reason the target followed the baseline. R2 checks each recorded judgment at its original prefix. Independent reconstruction of the square-test counts uses the admitted probe blocks. Block inclusion and ordering must be checked if completeness of the search account is claimed.

## Numerical reference

The [reference calculation](reference_kpis.py) was run with Python integer arithmetic. One search probe is one exact square test on $a^2-r$ at a center that passes the selected filter. The same product and primality checks assess the results of all three policies. The **fresh mask** policy constructs a mask on every compatible target. The **published mask** policy uses the already validated source mask after checking applicability. Both fall back to parity search on an incompatible target.

| Input | Parity probes | Fresh mask probes | Published mask probes | Result |
|---|---:|---:|---:|---|
| 1121, discovery source | 3 | 3 | 3 | Source uses parity search in all comparisons and yields 19 × 59 |
| 2929, compatible target | 6 | 4 | 4 | All yield 29 × 101. The published mask skips 59 and 61 and preserves the successful center 65 |
| 1643, incompatible target | 1 | 1 | 1 | Remainder 11 triggers fallback. Center 42 yields 31 × 53 |
| **Total including the source** | **10** | **8** | **8** | **Same factors in every policy** |

On 2929 pruning saves two of six square tests. Structural memoization saves one target-side mask construction relative to the fresh policy. The four remaining square tests and the applicability check are still necessary in this implementation. Modular membership tests, mask construction, reading a publication, proof checking, writing observations and replay have their own costs.

### How often the example helps

The reference calculation also covers every product of two distinct primes from 17 through 101 that is coprime to the source 1121. The resulting 153 targets include 2929 and 1643. Each target receives the same source-derived policy. Evidence from one test target is unavailable to the next. Known factors are used to define the evaluation population. The search receives only the target integer.

| Target-side indicator | Parity only | Fresh mask | Published mask |
|---|---:|---:|---:|
| Targets returning the same verified factors | 153 | 153 | 153 |
| Targets that use the residue filter | 0 | 16 | 16 |
| Targets that fall back after a signature mismatch | — | 137 | 137 |
| Exact square tests across all targets | 338 | 325 | 325 |
| Exact square tests on the 16 compatible targets | 40 | 27 | 27 |
| Targets requiring fewer square tests than parity search | — | 7 | 7 |
| Target-side mask constructions | 0 | 16 | 0 |
| Compatible source-mask reads | 0 | 0 | 16 |

Seven of the 16 compatible targets benefited from pruning. The other nine reached their factors before the mask could exclude a tested center. Across the full population the filter saved 13 of 338 square tests (3.85%). On the compatible subset it saved 13 of 40 (32.5%). Reuse replaced 16 target-side constructions with 16 reads. The source explored three moduli once. These counts establish where work changes on this finite population. Elapsed time and the break-even point require native measurements that charge discovery, publication, lookup and verification to the appropriate workload.

## Acceptance criteria for tracking and replay

| Native indicator | Acceptance condition for the 1121 → 2929 → 1643 fixture | Evidence |
|---|---|---|
| Governance with recoverable provenance | 1 of 1 expected policy changes resolves to the diagnosis, publication and previously active authority | Addresses and version transition |
| Target decisions with complete provenance | 2 of 2 expected target decisions explain the selected path and resolve to the input and active rules | One use of the published mask, one recorded fallback |
| Stability of the factor criterion | 1 distinct active factor-criterion address across the source and two target certificates | The three references and their admission prefixes |
| Paired control without activation | With the source and publication present, omit the proposal to activate the new policy. The original ontology must take 6 probes on 2929 and recover the same factors | Active version address and probe blocks for both runs |
| Replay of the untampered record | Every admitted event passes. Report the verified count and the exported event count | Original record and replay output |
| Rejection of altered evidence | Reject each fault injection at the affected judgment | Remove residues 1 and 9 from the proposed mask. Separately replace the pattern reference in a compatible target plan by a nonexistent address. Separately apply the published mask in the plan of the incompatible target 1643 |

The reference checker rejected the incomplete mask even though it still allows the successful source center 39. The native publication criterion also rejected this mutation at event 20. All the acceptance conditions above were exercised. The [native results and causal trace](README.md#observed-result) identify the record positions for each judgment and report the separate population outcomes.

To reproduce the arithmetic tables, run `python reference_kpis.py` from this directory. The program prints the selected mask, the individual probe sequences, the control outcome and the population counts.
