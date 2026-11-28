# Trace governed pattern reuse in integer factorization

Can a search explain which earlier failures caused it to skip two candidates on a new input? The source factors 1121 by Fermat search. Its recorded failures motivate a residue filter that a separate criterion checks and admits. A governing event can then install a search ontology that reads the filter. The target 2929 shares no prime factors with the source, so using the table transfers a search rule across instances. The incompatible target 1643 exercises the fallback.

## Observed result

Follow the certificate for 2929 backwards in the reuse record. Event **25** certifies 29 × 101 using the probe block at **24**. Its plan at **23** names the pattern published at **20** and the change at **21** that activated the new planning ontology. The publication cites diagnosis **19**, which identifies two failed centers, 35 and 37, in source block **17**. These are zero-based record positions. The criterion address of the factor certificate is the same before and after activation.

The parity and reuse records share their first 21 events, including publication. With the original ontology, the search on 2929 tests 55, 57, 59, 61, 63 and 65. After activation, it tests 55, 57, 63 and 65 and obtains the same factors. On 1643, the target's remainder is 11 modulo 16. Its fallback plan at **27** accounts for the single center 42 in block **28** and the certificate 31 × 53 at **29**.

A fourth run tests whether the source evidence is needed. The alternative source 1457 has the same remainder as 1121 modulo 16, but the first eligible center, 39, already yields 31 × 47. The driver then invokes diagnosis, publication and activation under the same initial rules as the reuse run. All three invocations leave the prefix unchanged. The target 2929 consequently uses the original ontology, tests six centers and returns 29 × 101. Replay verifies the 23 admitted events. The driver checks the three invocation outcomes at the source prefix and again at the end of the record: only the source can motivate a pattern, so the six failed probes of the target do not start a diagnosis.

| Native measure | Publication without activation | Fresh construction | Published mask reuse |
|---|---:|---:|---:|
| Search probes on the source and two targets | 10 | 8 | 8 |
| Events verified from genesis on that fixture | 29/29 | 30/30 | 30/30 |
| Search probes on the separate 153-target population | 338 | 325 | 325 |
| Target-side mask constructions in those searches | 0 | 16 | 0 |
| Compatible reads in the planning ontology | 0 | 0 | 16 |
| Population records passing full replay | 153/153 | 153/153 | 153/153 |

Pruning saved 13 square tests across the population (3.85%). Sixteen targets matched the signature and seven reached a center that the mask excluded before finding their factors. On those 16 targets the count fell from 40 to 27. Memoization replaced 16 fresh plan-side mask constructions with 16 reads. The plan criterion also consults the publication, and the probe criterion checks the entire reported block. Search counters exclude this verification work, publication and replay. Elapsed time was not benchmarked.

Four single-fault controls were checked at the affected event. Removing two allowed residues failed at publication **20**. A nonexistent pattern reference and an obsolete ontology address each failed at target plan **23**. Applying the published mask to 1643, whose remainder is outside its scope, failed at plan **27**. The archived controls include the judgment-only results, which test the retained evidence without regenerating the candidate.

## Reproduce the experiment

Use Python 3.12 or newer with this version of ZTES installed. From the repository root run `python -m pip install -e .` once. Then run the following from `examples/computability/factorization-patterns`.

```bash
python experiment.py --verify results/records.json.gz
python experiment.py --output reproduced
python population.py --check
```

The first command verifies the archived admissions and their causal references and re-derives the candidates. The second executes the three search policies and the alternative-source control from genesis and writes fresh records and measurements. The third runs each of the 153 target integers from its own copy of each policy's source prefix and compares the resulting counts and record tips with the archived manifest. The independent arithmetic reference, `python reference_kpis.py`, runs without ZTES.

## How to read the evidence

- **`parity`** follows the original planning ontology after the checked table has been published. This controls for the mere presence of the table.
- **`reuse`** follows the new planning ontology carried by the governance event. A compatible target reads the published table. A target whose remainder is outside its scope follows the parity rule. Every factor certificate is checked under the same factor criterion.
- **`fresh`** constructs the same table on demand. Comparing its search probes with `parity` measures pruning. Comparing it with `reuse` identifies the target-side construction that the published table replaces.
- **`no_trigger`** uses the alternative source 1457. Its invocation log in `results/results.json` records the three calls at the source prefix and at the end of the record. The archived event sequence identifies the ontology that governed the subsequent target.

The [design and acceptance criteria](DESIGN.md) define the discovery rule, controls and counting boundaries. The [fixture results](results/results.json) give the event coordinates, governing addresses, search paths and replay outcomes. The [population manifest](results/population.json) gives the number, factors, square-test counts and native record tip for each policy and input. Each compatible target still checks its signature and produces its own evidence.
