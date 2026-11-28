# Trace governed changes in Goldbach representations

Why does the same query for 20 have four witnesses at one prefix and three at another? In this finite Goldbach example, two independently governed sources supply the eligible prime addends. A number-theoretic transform (NTT) computes the counts for every sum. One admitted change restricts the second addend to at most 13. Each query answer records all its ordered witnesses and can be checked against the rules that governed it.

## Follow the answer for 20

In the archived `governed_reuse` execution, event **24** admits (3,17), (7,13), (13,7) and (17,3). The witness (3,17) satisfies the predeclared condition for proposing the right-hand restriction. Event **25** cites that answer. Its admission under the preceding authority activates the new right-hand ontology and criterion. Event **26** records the six primes eligible on the right under the new rule.

For the second query, product **29** uses the **original left spectrum at 21** and the **new right spectrum at 28**. Answer **30** admits (7,13), (13,7) and (17,3). The answer criterion keeps its original address. Replay also validates the four witnesses at event 24 under their original rules. Event positions here are zero-based.

## Results and controls

| Archived execution | First query and pair count | Second query and pair count | Forward NTTs for second query | Earlier spectra used | Events passing full replay |
|---|---|---|---:|---|---:|
| `unchanged` | 20 → 4 | 20 → 4 | 0 | left and right | 28/28 |
| `governed_reuse` | 20 → 4 | 20 → 3 | 1 | left | 31/31 |
| `governed_fresh` | 20 → 4 | 20 → 3 | 2 | none | 32/32 |
| `no_trigger` | 4 → 1 | 20 → 4 | 0 | left and right | 28/28 |

The unchanged and governed-reuse records have the same first 25 events. The fresh and reuse arms share their first 27 events, including the change and the new right-hand input. Their second queries request different materialization policies and produce identical coefficient vectors and witnesses. In the no-trigger control, (2,2) supplies no evidence for restricting the right addend. The attempted activation at prefix length 25 produces no admission. The driver reports that invocation separately and rechecks it at the saved prefix. After the second query the answer for 20 exhibits (3,17), and at the end of the record the change is proposed and admissible; the driver checks this without appending it. Evidence, not the schedule of the calls, decides whether the rule can change.

Direct enumeration confirmed all 64 coefficient slots in each of eight products. Both sources initially contain the eight primes up to 20. Restricting the second addend to at most 13 reduces the number of eligible ordered pairs from **50 to 36** across even sums and from **64 to 48** across all sums. Twelve sums changed count. Three sums, **34, 36 and 38**, lost their final witness within this prime horizon. The coefficient for 4 stayed at one.

Reusing the left spectrum saved one 64-point forward transform on the governed query. Both governed arms still performed one inverse transform and their product criteria independently enumerated all 48 eligible pairs. The forward counts come from tracing the recorded proposal code during re-derivation. The fixture measures operations and evidence; it does not establish a wall-clock speedup. Each query asks for a new product, even when both operand spectra can be reused.

## Reproduce the four records

Use Python 3.12 or newer. From the repository root, install the project with `python -m pip install -e .`. Then run the following from `examples/computability/goldbach-governed-convolution`.

```bash
python experiment.py --verify results/records.json.gz
python experiment.py --output reproduced
```

Verification checks both the admission judgments and candidate re-derivation, resolves the version and operand references, and compares every coefficient with direct integer enumeration. Regeneration executes all four schedules using the native ZTES executor. The archive includes the outcomes of controls that present an obsolete right spectrum and altered witness evidence to their local criteria.

The [design](DESIGN.md) gives the algebra, governance condition and counting boundaries. The [results](results/results.json) report the event positions, version addresses, transform counts and fault outcomes. The [compressed archive](results/records.json.gz) contains the four complete append-only records, including the executable specifications. The native lineages are `catalog`, `left`, `right`, `query`, `spectrum`, `product`, `answer` and `activate`.
