# Supply dispute experiment

Both target runs admitted 45 primary units and 20 supplemental units for the same beneficiary. They used identical local observations and active specifications. The warm target reused the graph published after the source paid 60 + 30. The exclusion kept that graph available and prevented payment.

| Case | New partial graphs expanded | Complete plans tested in search | Published candidates inspected | All symbolic checks¹ | All numeric bindings¹ | Outcome |
|---|---:|---:|---:|---:|---:|---|
| cold | 7 | 4 | 0 | 5 | 2 | 45 + 20 |
| warm | 0 | 0 | 1 | 2 | 2 | 45 + 20 |
| exclusion | 0 | 0 | 1 | 2 | 2 | payment refused |
| stricter | 7 | 4 | 1 | 5 | 2 | 45 + 20 |
| version_change | 6 | 3 | 1 | 4 | 2 | 45 + 20 |
| unpublished | 7 | 4 | 0 | 5 | 2 | 45 + 20 |

¹ Counted inside the executed ZTES libraries during target plan derivation, plan admission and settlement. The plan criterion independently rechecks the graph and its binding. Each run also invoked the plan criterion once and the settlement criterion once in this window. Replay and fault probes are excluded from the counts.

Source construction expanded 7 partial graphs and tested 4 complete candidates. The four-node graph allocates primary cover, calculates the residual, allocates supplemental cover and credits the beneficiary. In the version-change control the target uses a different search order. In the stricter control it requires an additional independent review. Both obtain a fresh valid graph.

## Timing

60 matched batches in one process, rotating the execution order. Python 3.12.14 on Windows-11-10.0.22631-SP0. Reported values are median milliseconds. Timed runs have instrumentation disabled. The earlier acceptance runs warm the interpreter.

| Schedule | A constructs plan | A publishes | B snapshot, plan and settlement | A and B together |
|---|---:|---:|---:|---:|
| cold | 0.598 | 0.244 | 0.948 | 3.840 |
| warm | 0.600 | 0.251 | 0.735 | 3.615 |
| unpublished | 0.597 | 0.000 | 0.943 | 3.589 |

The median paired target saving (cold minus warm) was 0.210 ms. The warm target was faster in 57/60 batches. For the whole two-case workload, the median saving (unpublished minus warm) was -0.053 ms, with warm faster in 26/60 batches. Negative savings mean greater cost. The two-case comparison charges publication to the warm run. It includes boundary inputs and judgments, and excludes initialization, replay, controls and file I/O. Fresh search also builds and records a longer derivation trace. Timings include that serialization and hashing work. These local timings describe this fixture.

## One publication across several targets

Each batch compares a source that publishes once with a source that never publishes. Both then process the same eight distinct cold-chain cases, with their own parties, contracts and amounts. Each row measures the whole workload from the first source observation through the stated target, including publication when enabled. The three rows are cumulative observations of the same runs.

| Targets after A | Complete fresh plans without / with publication | Median ms without publication | Median ms with publication | Median paired saving (ms) | Faster with publication |
|---:|---:|---:|---:|---:|---:|
| 1 | 4 / 0 | 3.547 | 3.559 | -0.016 | 11/24 |
| 4 | 16 / 0 | 9.170 | 8.374 | 0.758 | 24/24 |
| 8 | 32 / 0 | 17.572 | 15.587 | 1.666 | 24/24 |

## Causal checks

- In the warm record, transport diagnosis 26 cites base event 25. Cold-chain diagnosis 37 cites base event 36. Their projected signatures agree. Each specialized diagnosis remained pending on the separate funding-only control.
- Target settlement 40 uses publication `catalogue/1`. Changing its reference in a copy caused full replay to reject precisely that event. A duplicate submission and a dangling reference were also refused by the local settlement criterion.
- Governance event 33 activated new specification versions under prior authority. The fixed-regime certificate bounds cover at 60 for a loss of 90. The funded new regime paid 60 + 30. The waiting control has a continuation paying 90 under the original regime.
- The coverage criterion refused premature closure. Event 38 closed compensation after the carrier's refund of 2 and the supplier's refund of 7.

Full replay from genesis passed on all 13 exported records, including the valid prefix with incomplete compensation. Entries for the fixed, incomplete and completed governance runs include shared prefixes. Rejected attempts are reported separately from ledger events.

| Record | Admitted events including specifications and genesis | Full replay (ms, single run) |
|---|---:|---:|
| cold | 41 | 70.554 |
| warm | 41 | 70.268 |
| exclusion | 40 | 69.863 |
| stricter | 42 | 71.707 |
| version_change | 41 | 72.196 |
| unpublished | 40 | 75.118 |
| funding_only | 25 | 82.501 |
| governance_waiting | 26 | 17.954 |
| governance_fixed | 33 | 18.112 |
| governance_incomplete | 37 | 25.345 |
| governance_complete | 39 | 24.151 |
| series_cold_8 | 110 | 88.126 |
| series_warm_8 | 111 | 86.613 |

Raw evidence and per-batch samples are in [results.json](results.json). The [record archive](records.json.gz) includes the executable specifications.
