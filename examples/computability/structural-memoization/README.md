# Structural memoization across two dispute models

Can solving a transport-damage claim save work on a cold-chain claim while leaving the latter responsible for its own evidence and payment decision? The experiment tests three conditions. The target must identify a previously constructed plan through a common abstraction, skip a measurable part of the search, and retain the ability to refuse payment. A separate timing comparison asks how often the plan must be used for its publication cost to pay off in this workload.

The source case settles a loss of 90 using 60 units of primary cover and 30 from a guarantee. The target establishes a different loss of 65 and pays 45 + 20. A third fixture makes the same guarantee inapplicable to the diagnosed cause. It finds the same plan, proposes the same amounts and refuses payment. [Full design](DESIGN.md) · [Recorded results](results/RESULTS.md)

## From an event to a reusable pattern

| Concept | Meaning in this model |
|---|---|
| Event identity | An admitted event has an immutable coordinate and payload. An eligible consumer can read that occurrence again. Equal amounts in two settlements still belong to two distinct events. |
| Pattern | The reusable object is a typed, parameterized graph of operations. It specifies roles, dependencies and conditions on amounts. Its publication cites the source diagnosis, derivation and payment. |
| Analogy | The transport and cold-chain diagnoses are admitted by different abstractions. Each projects to the same signature in their common executable ancestor, the funding abstraction. Equality of these projections identifies a structural problem on which both diagnoses agree. |
| Structural memoization | For a fixed signature and compatible construction versions, a deterministic planner produces a graph. The target can retrieve that graph by its publication reference and avoid constructing it again. It must still bind and verify its own parties, amounts and coverage. |

Transport damage requires consignment and inspection evidence. A cold-chain breach requires a temperature observation tied to the lot, a calibration record and a quality determination. Their common signature specifies primary-first funding, compatible units and a nominated supplemental instrument. If the recognized obligation is $D$, the primary limit $S$ and the supplemental limit $G$, this example covers $0 < S < D \le S+G$. With only the generic funding evidence, the common abstraction admits a summary while each specialized diagnosis remains pending. This realizes the comparison in §5.4, Definition 12, of the OEE manuscript.

The common abstraction, its reductions and the primitive operations are supplied. What execution constructs is the four-operation plan. The use of a prior derivation to guide another case has a precedent in *derivational analogy*. The contribution illustrated here is its executable connection to publication, declared visibility, local admission and full replay in ZTES. [Veloso and Carbonell, 1993](https://doi.org/10.1023/A:1022686910523)

## Method

1. **Construct.** Begin with an empty catalogue. The source planner enumerates well-typed graphs, including single-source and reversed-order attempts. A symbolic checker verifies that the selected graph allocates the primary cover, computes the residual, allocates that residual to the guarantor and credits the beneficiary. Across the declared signature the two draws obey their limits and sum to $D$.
2. **Publish.** Once the source settlement is admitted, the catalogue validates and records the graph and its provenance. In the archived warm record the publication has the reference `catalogue/1`. The target ontology can read it through a declared catalogue snapshot.
3. **Compare.** Use the same target observations, active specifications and invocation order twice. The *cold* target fixes its snapshot before publication. The *warm* target fixes its snapshot afterwards. By planning time the publication exists in both records. Only the warm target can use it. Count fresh graph expansions, completed plans and independent checks.
4. **Exercise the boundary.** Change only the local guarantee coverage to obtain the exclusion fixture. Separately change the required certification or the planner version and check that the target performs a fresh search. Alter the publication reference in a copy of an admitted payment and run full replay from genesis.

In the S1 architecture the active criterion judges each completed candidate on the target prefix. R1 governs changes of authority. R2 permits checking recorded admissions against the versions in force at their original prefixes. The main comparison keeps these rules fixed. A companion system exercises an actual governed change and requires refunds for all affected actors before compensation can close. [Reuse system](native/reuse/system.json) · [Governance system](native/governance/system.json)

S1 specifies the execution contract that different infrastructures can implement. For two realizations of the same specifications, Theorem 3 (§4.7) gives corresponding finite admitted traces when a map preserves the contract, initial contexts and active versions correspond, and paired bound invocations remain in the comparison domain. In this fixture the rules and schedules are effective and the boundary observations are computable, so a Turing machine is one possible realization of each run.

## Results against the objectives

| Target operation or outcome | Cold | Warm | Warm with exclusion |
|---|---:|---:|---:|
| Fresh partial graphs expanded | 7 | 0 | 0 |
| Completed plans tested in fresh search | 4 | 0 | 0 |
| Symbolic checks including plan admission | 5 | 2 | 2 |
| Numeric bindings including plan admission | 2 | 2 | 2 |
| Final payment | 45 + 20 | 45 + 20 | Refused |

The cold and warm runs compute the same target allocation. The warm run saves work by reading the published source graph and skipping the search that selected it. The two remaining symbolic checks and two numeric bindings show the work performed on reuse. The admission objective is tested by the exclusion, which leaves the structural signature intact. The rule-change controls also exercise conservative reuse. A stricter certification requires four fresh candidate tests. Changing the enumeration order requires three, produces a different trace and reaches the same settlement. Full replay accepted all 13 archived sequences, some of which share prefixes, and rejected the modified payment at its own event.

The archived target-only comparison used 60 matched batches. Warm execution was faster in 57, with a median paired saving of 0.210 ms. Charging publication to the complete source-plus-one-target workload gave a median paired saving of −0.053 ms. A separate series varied the number of subsequent targets, using distinct contracts, lots, parties and amounts. Each row below is a cumulative checkpoint within the same 24 paired series.

| Subsequent targets | Fresh plans tested without / with publication | Median paired whole-workload saving | Pairs faster with publication |
|---:|---:|---:|---:|
| 1 | 4 / 0 | −0.016 ms | 11/24 |
| 4 | 16 / 0 | 0.758 ms | 24/24 |
| 8 | 32 / 0 | 1.666 ms | 24/24 |

For one target, avoided search did not consistently recover the cost of publication. At four and eight targets the median saving over the whole workload was positive. In the archived series every pair at four and eight targets was faster; in three runs on a second machine (Linux, Python 3.13) 15 to 22 of 24 pairs were faster at four targets and 18 to 23 of 24 at eight. The number of complete plans the targets did not test, 4 per target and 32 for eight targets, does not depend on the machine. These measurements include creating, serializing and hashing the longer fresh-search trace. They describe one machine, one structural signature, a four-operation graph and synthetic, case-specific balances. The experiment leaves open how to discover new common abstractions and how large a catalogue can grow before retrieval dominates. [Raw measurements and control outcomes](results/results.json) · [Archived records](results/records.json.gz)

## One thread: reuse under governed change

The [thread](thread/DESIGN.md) puts reuse and governance in one record of ordinary systems. The observations are declared constants, so `python -m ztes run` executes each system, under the agenda and under workers. A case may draw on ordered tiers of payment, and the rules in force let the first K pay.

* **Cost.** For k = 2 … 5 tiers a fresh derivation tests 4, 15, 64 and 325 complete plans under a planner that leaves the priority rule to the checker, and 3, 6, 10 and 15 under one that drops refused plans. The plan criterion checks these counts. A reuse costs one proof in the ontology and one in the criterion under either planner.
* **Visibility.** A case reads only the publications of the precedents its policy declares. A control that declares none derives its plan although a matching pattern exists.
* **Governance.** A pattern carries the versions under which it was derived. After a certified obstruction, a decision of the review board and a governed change of the rules, a pattern of the earlier rules is used only after a new proof under the new versions. Refunds link each affected party to its earlier debits, and the closure needs all of them.

Each claim has its test. [Regions](thread/regions/system.json) · [Scaling](thread/scaling/system.json) · [Scaling, pruned](thread/scaling-pruned/system.json) · [Governed](thread/governed/system.json)

## Reproduce from the repository root

Use Python 3.12 or later. The archival timings and records above were produced with ZTES revision `d49981a3`. This repository integration targets `f7b6de7`; a fresh run on it regenerates the archived records exactly, on Windows and on Linux (`test_published_executions_replay_and_can_be_reproduced`). The archive retains the specifications used to produce each event. The first verification below replays that archive using the installed checkout. The final two commands generate and verify a fresh run in a separate output directory.

```bash
python -m pip install -e ".[test]"
python -m ztes check examples/computability/structural-memoization/native/reuse
python -m ztes check examples/computability/structural-memoization/native/governance
python -m unittest discover -s examples/computability/structural-memoization -v
python examples/computability/structural-memoization/experiment.py --verify examples/computability/structural-memoization/results/records.json.gz
python examples/computability/structural-memoization/experiment.py --pairs 60 --series-pairs 24 --output ../structural-memoization-run
python examples/computability/structural-memoization/experiment.py --verify ../structural-memoization-run/records.json.gz
```

The driver supplies the boundary observations and invocation schedule to the in-process ZTES services. The two systems under `native/` are manifests of the recorded specifications: they have no plan of their own, so `python -m ztes run` on them only registers the specifications (21 and 23 events), and the executions are those of the driver. A fresh run writes a readable report, raw JSON samples and the compressed event records with their executable specifications. [Experiment driver](experiment.py) · [Plan search and checker](planner.py) · [Multi-target experiment](amortization.py)
