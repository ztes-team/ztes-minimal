# Trace governed changes in Goldbach representations

## Question

Can an admitted change to one input rule alter a computed relation while preserving the evidence for its previous value? A second question concerns reuse. When the right-hand rule changes, which intermediate result can a later computation still use, and what recorded evidence justifies that choice?

The [E7 Goldbach experiment](../../../experiments/e7-fates/goldbach/DESIGN.md) checks successive even integers for a prime-pair witness. Here the input horizon is finite and the two positions in a pair have independently specified roles. The result includes the number of eligible **ordered** pairs for each sum. Changing the eligibility of the second addend changes the relation computed over that horizon. Every numerical claim below refers to this finite relation.

## What a coefficient means

Let both inputs initially contain the primes in the interval from 2 to 20, namely 2, 3, 5, 7, 11, 13, 17 and 19. Write $A_i$ and $B_j$ for the left and right eligibility indicators. The coefficient at sum $s$ is

$$
c_s=\sum_{i+j=s} A_i B_j.
$$

Each term equal to one denotes a specific pair of eligible addends. A criterion can check the entire coefficient vector by direct counting and check a query answer by enumerating its witnesses. Checking only that each listed pair adds to the requested sum would allow an incomplete answer.

The proposer computes the linear convolution by a number-theoretic transform (NTT). Padding to length 64 covers degrees 0 through 40, including all possible sums of inputs bounded by 20. With modulus 257, the scalar 3 generates the multiplicative group and $3^4$ has order 64. Each coefficient is at most eight, so the residue determines its exact integer value. The transform settings and the input to which a spectrum belongs are part of the evidence for reuse.

Counting prime-pair sums by NTT has an established numerical basis. This experiment studies what happens to the operands, witnesses and their authority when an eligibility rule changes during execution. [Jesus, Oliveira e Silva and Weiland, 2023](https://doi.org/10.1002/cpe.7882)

## The change of authority

The supplied governance policy permits a restriction after an admitted answer exhibits a witness whose second addend exceeds 13. The replacement right-hand rule allows only primes at most 13. The governance event must cite the triggering evidence and carry the replacement specification under prior authority. Its position separates the two regimes. Earlier answers retain the rules and witnesses under which they were admitted.

Under the initial rules, 20 has the four ordered witnesses (3,17), (7,13), (13,7) and (17,3). The first exposes the premise of the change. Applying the right-hand rule removes (3,17) while preserving (17,3). This asymmetry lets the experiment detect a mistaken implementation that also restricts the left operand. It also distinguishes publication of evidence from activation of a new rule.

| Sum | Initial count | Count after the right-hand restriction | Reason |
|---:|---:|---:|---|
| 4 | 1 | 1 | Both positions still allow 2. |
| 20 | 4 | 3 | Only the witness with 17 in the second position loses eligibility. |
| 38 | 1 | 0 | The original witness (19,19) loses its right addend. The largest permitted sum in the new regime is 19 + 13. |

## Controls and accounting

Use matched executions for the original query and the governed query. Preserve the source observations and record which invocation supplies the intervention in each arm.

- Withhold activation after the same first answer. Repeating the query for 20 must still return four witnesses.
- Admit the change and use a compatible prior left spectrum. The new right spectrum must derive from a right input admitted under the new rules.
- Admit the same restriction and rebuild the operands. The resulting coefficient vector and witness set must agree with the reuse arm.
- Start with the query for 4. It has one witness, (2,2). Invoking the governance mechanism at that prefix must leave the old right rule active. A later query for 20 must still have four witnesses. Its answer exhibits (3,17), so at the end of that record the change must be proposed and admissible. Log both observations separately from admitted events.

Count forward-transform evaluations during proposal, inverse-transform evaluations, and reuse separately. Verification may perform additional arithmetic. For the entire initial spectrum, direct enumeration produces 64 ordered pairs. The successor spectrum contains 48. At even sums the corresponding counts are 50 and 36. These totals count pairs across queries; the witness counts for a single sum are given above. With only eight source primes, direct enumeration also provides a small independent reference implementation.

## What to check in the record

Trace a post-change answer through its coefficient vector to the two spectra used in producing it. On the right, follow the reference to the successor input and the event that authorized its rule. On the left, identify the earlier input and compatible transform. Verify the old answer at the prefix preceding its admission. Reject an obsolete right operand offered for the successor computation, even when that same operand was valid at its original prefix. Reject an answer that omits an eligible witness even when each remaining witness is valid. The [experiment report](README.md) gives the archived outcomes, counts and commands for replay.
