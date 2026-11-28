"""Run three native executions per semiprime and verify their records from genesis."""

import argparse
import json
from itertools import combinations
from math import gcd
from pathlib import Path

from ztes.substrate import events
from ztes.substrate.replay import verify

from experiment import run_targets, source_prefix, target_metrics
from reference_kpis import is_prime


MODES = ("parity", "fresh", "reuse")
ARCHIVE = Path(__file__).resolve().parent / "results" / "population.json"


def target_pairs():
    primes = [n for n in range(17, 102) if is_prime(n) and gcd(n, 1121) == 1]
    return combinations(primes, 2)


def one_target(prefix, n, expected):
    record = run_targets(prefix, [n])
    if record[:len(prefix)] != prefix:
        raise ValueError(f"Source prefix changed for {n}")
    faults = verify(record)
    if faults:
        raise ValueError(f"Replay failed for {n}: {faults[0]}")
    row, = [r for r in target_metrics(record) if r["n"] == n]
    if tuple(row["factors"]) != expected:
        raise ValueError(f"Wrong factors for {n}: {row['factors']}")
    return row, events.link(record)


def run_population():
    prefixes = {mode: source_prefix(mode) for mode in MODES}
    counts = {mode: dict(square_tests=0, compatible_square_tests=0, mask_builds=0,
                         mask_reads=0, replays_passed=0) for mode in MODES}
    rows = []
    compatible = improved = 0
    for p, q in target_pairs():
        n = p * q
        results = {}
        tips = {}
        for mode in MODES:
            results[mode], tips[mode] = one_target(prefixes[mode], n, (p, q))
        hit = results["reuse"]["path"] == "reuse"
        if hit != (n % 16 == 1) or hit != (results["fresh"]["path"] == "fresh"):
            raise ValueError(f"Wrong scope for {n}")
        if results["fresh"]["probes"] != results["reuse"]["probes"]:
            raise ValueError(f"Search changed between fresh and reused masks for {n}")
        probes = {mode: len(results[mode]["probes"]) for mode in MODES}
        compatible += int(hit)
        improved += int(probes["reuse"] < probes["parity"])
        for mode, row in results.items():
            totals = counts[mode]
            totals["replays_passed"] += 1
            totals["square_tests"] += probes[mode]
            if hit:
                totals["compatible_square_tests"] += probes[mode]
            totals["mask_builds"] += row["target_builds"]
            totals["mask_reads"] += row["pattern_reads"]
        rows.append(dict(n=n, factors=[p, q], compatible=hit, square_tests=probes,
                         record_tips=tips))
    return dict(targets=len(rows), compatible=compatible, incompatible=len(rows) - compatible,
                fewer_square_tests=improved, modes=counts, cases=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true", help="save the calculated case manifest")
    action.add_argument("--check", action="store_true", help="compare every case with the archive")
    args = parser.parse_args()
    result = run_population()
    if args.write:
        ARCHIVE.parent.mkdir(exist_ok=True)
        ARCHIVE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.check and result != json.loads(ARCHIVE.read_text(encoding="utf-8")):
        raise SystemExit("Population differs from the archived results")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
