"""Run the supply dispute experiment, or independently replay its exported ZTES records."""

import argparse
import gzip
import json
import platform
import sys
from copy import deepcopy
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from ztes.model import judge
from ztes.substrate import ADMITTED, FALSE, lookups
from ztes.substrate.replay import verify
from runtime import admitted, full_replay, initial_specifications, new_executor, require, timed


def export_systems(destination):
    """Materialize the domain specifications for the repository's native System loader."""
    from governance import governance_system
    from ztes.system.system import System

    pairs = initial_specifications()
    specs = {f"{s['abstraction']}/{s['role']}.v{s['version']}": s for pair in pairs for s in pair}
    definition = {"system": "supply-dispute", "abstractions": [c["abstraction"] for c, _ in pairs],
                  "plan": [{"phase": 1}, {"phase": 2}, {"phase": 3}], "specifications": specs}
    for name, model in (("reuse", System.from_dict(definition)), ("governance", governance_system())):
        design = (Path(__file__).with_name("native") / name / "DESIGN.md").read_text(encoding="utf-8")
        saved = model.save(destination / name, design=design)
        problems = saved.check(log=lambda _: None)
        require(not problems, (name, problems))
        require(saved.specs == model.specs, f"{name} specification changed on export")
        if name == "reuse":
            require(all(saved.specs[key] == spec for key, spec in specs.items()), "expanded definitions differ")


def observe(executor, case, **options):
    from case_model import fixture_inputs

    for lineage, observation in fixture_inputs(case, **options):
        admitted(executor, lineage, observation)
    admitted(executor, "base")
    return admitted(executor, "transport" if case == "A" else "cold_chain")


def direct_judgment(prefix, lineage, candidate):
    version = lookups.active(prefix, lineage, "criterion")
    return judge(prefix, lookups.load(prefix, version), candidate)


def observed_helpers(counts, action, *args):
    """Count calls in the actual recorded ZTES libraries only on the acceptance runs."""
    if counts is None:
        return action(*args)
    previous = sys.getprofile()

    def count(frame, event, arg):
        code = frame.f_code
        if event == "call" and code.co_filename == "<library>" and code.co_name in counts:
            counts[code.co_name] += 1

    sys.setprofile(count)
    try:
        return action(*args)
    finally:
        sys.setprofile(previous)


def run_case(mode, *, controls=True):
    executor = new_executor()
    workload_start = perf_counter_ns()
    source_diagnosis = observe(executor, "A")
    admitted(executor, "snapshot")
    source_plan, source_search_ms = timed(admitted, executor, "plan")
    source_payment = admitted(executor, "settle")
    publication, publish_ms = None, 0.0
    if mode not in ("cold", "unpublished"):
        publication, publish_ms = timed(admitted, executor, "catalogue")

    target_diagnosis = observe(executor, "B", excluded=mode == "exclusion", stricter=mode == "stricter",
                               revised=mode == "version_change")
    snapshot, snapshot_ms = timed(admitted, executor, "snapshot")
    if mode == "cold":
        # The object exists by the time both targets plan. Only its membership in B's cut differs.
        publication, publish_ms = timed(admitted, executor, "catalogue")
    counts = (dict.fromkeys(("extensions", "proof_error", "bind_graph", "compatible_pattern",
                             "plan_valid", "settlement_valid"), 0) if controls else None)
    plan, planning_ms = timed(observed_helpers, counts, admitted, executor, "plan")
    prefix = executor.prefix()
    (status, candidate), admission_ms = timed(observed_helpers, counts, executor.execute, "settle")
    workload_ms = (perf_counter_ns() - workload_start) / 1_000_000
    require(status == (FALSE if mode == "exclusion" else ADMITTED), (mode, status, candidate))
    require((source_payment["primary"], source_payment["supplemental"]) == (60, 30), source_payment)
    require((candidate["primary"], candidate["supplemental"], candidate["credit"]) == (45, 20, 65), candidate)
    reuse = mode in ("warm", "exclusion")
    require(plan["publication"] == (publication["ordinal"] if reuse else 0), (mode, plan))
    require(plan["metrics"]["tested"] == 0 if reuse else plan["metrics"]["tested"] > 0, plan["metrics"])

    checks = {}
    if controls:
        checks["local_criterion_accepts_candidate"] = direct_judgment(prefix, "settle", candidate)
        require(checks["local_criterion_accepts_candidate"] == (status == ADMITTED), (mode, checks))
        invalid = dict(candidate, publication=9999)
        checks["dangling_reference_refused"] = not direct_judgment(prefix, "settle", invalid)
        require(checks["dangling_reference_refused"], "dangling pattern reference accepted")
        if status == ADMITTED:
            after = executor.prefix()
            checks["duplicate_refused"] = not direct_judgment(after, "settle", candidate)
            duplicate_status, _ = executor.execute("settle")
            require(duplicate_status != ADMITTED and len(executor.prefix()) == len(after)
                    and checks["duplicate_refused"], "duplicate settlement")
        else:
            checks["attempt_appended_nothing"] = len(prefix) == len(executor.prefix())
            require(checks["attempt_appended_nothing"], "excluded settlement was recorded")

    record = list(executor.prefix())
    measures = {"source_plan_ms": source_search_ms, "publication_ms": publish_ms,
                "target_snapshot_ms": snapshot_ms, "target_plan_ms": planning_ms,
                "target_admission_ms": admission_ms,
                "target_path_ms": snapshot_ms + planning_ms + admission_ms, "workload_ms": workload_ms}
    report = {"source_diagnosis": source_diagnosis, "target_diagnosis": target_diagnosis,
              "source_plan": source_plan, "source_payment": source_payment,
              "publication": publication, "snapshot": snapshot, "target_plan": plan,
              "settlement_status": status, "target_candidate": candidate,
              "local_checks": checks, "helper_calls_in_target_plan_and_settlement": counts,
              "settlement_prefix_length": len(prefix)}
    return report, record, measures


def target_inputs(record):
    return [e["payload"] for e in record if e["coord"]["kind"] == "exec"
            and e["coord"]["abstraction"] in ("funding", "policy", "evidence")
            and e["payload"].get("case") == "B"]


def check_ancestor(record):
    """Resolve both reductions using only admitted events earlier than each diagnosis."""
    parents = {}
    reductions = {}
    for event in record:
        coord, payload = event["coord"], event["payload"]
        if coord["kind"] != "exec":
            continue
        if coord["abstraction"] == "base":
            parents[payload["ref"]] = event
        elif coord["abstraction"] in ("transport", "cold_chain"):
            parent = parents[payload["base_ref"]]
            require(parent["payload"]["case"] == payload["case"] and
                    parent["payload"]["signature"] == payload["signature"], "invalid reduction to ancestor")
            reductions[coord["abstraction"]] = {"case": payload["case"], "base_event": parent["coord"]["n"],
                                                "diagnosis_event": coord["n"], "signature": payload["signature"]}
    transport, cold_chain = reductions["transport"], reductions["cold_chain"]
    require(transport["signature"] == cold_chain["signature"] and
            transport["base_event"] != cold_chain["base_event"], "missing cross-abstraction match")
    return reductions


def refinement_witnesses():
    """Generic funding is admissible while each higher diagnosis still lacks its own evidence."""
    from case_model import fixture_inputs

    executor = new_executor()
    witnesses = {}
    for case, higher in (("A", "transport"), ("B", "cold_chain")):
        funding = next(value for name, value in fixture_inputs(case) if name == "funding")
        admitted(executor, "funding", funding)
        base = admitted(executor, "base")
        n = len(executor.prefix())
        status, _ = executor.execute(higher)
        require(status == "Not Yet" and len(executor.prefix()) == n, f"{higher} admitted without evidence")
        witnesses[higher] = {"base_ref": base["ref"], "base_event": n - 1,
                             "higher_status": status, "prefix_length": n}
    return witnesses, list(executor.prefix())


def check_comparison(cases, records):
    cold, warm = cases["cold"], cases["warm"]
    common_inputs = target_inputs(records["cold"])
    require(common_inputs and common_inputs == target_inputs(records["warm"]), "target inputs changed")
    cold_specs = [e for e in records["cold"] if e["coord"]["kind"] == "spec"]
    warm_specs = [e for e in records["warm"] if e["coord"]["kind"] == "spec"]
    require(cold_specs and cold_specs == warm_specs, "governing specifications differ")
    for field in ("case", "beneficiary", "primary", "supplemental", "credit", "policy_ref", "evidence"):
        require(cold["target_candidate"][field] == warm["target_candidate"][field], f"mismatch: {field}")
    require(warm["source_plan"]["graph"] == warm["publication"]["graph"] == warm["target_plan"]["graph"]
            == cold["target_plan"]["graph"], "plans differ")
    require(warm["publication"]["plan_ref"] == warm["source_payment"]["plan_ref"], "wrong source plan")
    require(warm["target_plan"]["metrics"]["expansions"] < cold["target_plan"]["metrics"]["expansions"],
            "no structural search avoided")
    require(cases["exclusion"]["target_plan"]["graph"] == warm["target_plan"]["graph"], "exclusion graph differs")
    require(cold["snapshot"]["visible"] == [] and warm["snapshot"]["visible"] == [warm["publication"]["ordinal"]],
            "catalogue snapshots did not isolate visibility")
    require(cases["unpublished"]["target_plan"]["trace"] == cold["target_plan"]["trace"], "fresh baselines differ")
    revised = cases["version_change"]["target_plan"]
    require(revised["versions"]["planner"] != warm["publication"]["versions"]["planner"]
            and revised["trace"] != cold["target_plan"]["trace"] and revised["graph"] == warm["target_plan"]["graph"],
            "changed construction version was not exercised")
    for case in cases.values():
        calls = case["helper_calls_in_target_plan_and_settlement"]
        require(calls["extensions"] == case["target_plan"]["metrics"]["expansions"] and
                calls["plan_valid"] == calls["settlement_valid"] == 1, "missing observed planner or judgment")
    # The target payment is the last admitted event. Its predecessor hash stays valid in this fault.
    altered = deepcopy(records["warm"])
    n = warm["settlement_prefix_length"]
    require(n == len(altered) - 1 and altered[n]["coord"]["abstraction"] == "settle", "unexpected tamper target")
    altered[n]["payload"]["publication"] += 1000
    findings = verify(altered)
    require(len(findings) == 1 and findings[0][0] == n and "realization" in findings[0][1],
            "full replay failed to distinguish the altered derivation")
    return {"reductions": check_ancestor(records["warm"]),
            "identical_local_observations": len(common_inputs), "identical_specs": True,
            "same_target_settlement": True, "same_plan_graph": True, "tampered_event": n,
            "replay_rejection": findings[0][1]}


def benchmark(pairs):
    # Rotate the three positions and reverse on alternating blocks to balance order effects.
    orders = [("cold", "warm", "unpublished"), ("warm", "unpublished", "cold"),
              ("unpublished", "cold", "warm")]
    samples = {mode: [] for mode in orders[0]}
    for p in range(pairs):
        order = orders[p % len(orders)]
        for mode in (order if (p // len(orders)) % 2 == 0 else reversed(order)):
            _, _, measurements = run_case(mode, controls=False)
            samples[mode].append(measurements)
    medians = {mode: {key: median(x[key] for x in rows) for key in rows[0]}
               for mode, rows in samples.items()}
    differences = [c["target_path_ms"] - w["target_path_ms"]
                   for c, w in zip(samples["cold"], samples["warm"])]
    workloads = [u["workload_ms"] - w["workload_ms"] for u, w in zip(samples["unpublished"], samples["warm"])]
    return {"pairs": pairs, "clock": "perf_counter_ns", "unit": "ms", "medians": medians,
            "paired_target_saving_median_ms": median(differences),
            "paired_two_case_saving_median_ms": median(workloads),
            "batches_with_lower_warm_workload_time": sum(x > 0 for x in workloads),
            "pairs_with_lower_warm_target_time": sum(x > 0 for x in differences), "samples": samples}


def write_results(destination, summary, records):
    destination.mkdir(exist_ok=True, parents=True)
    # Each archive includes the active specifications, embedded functions, boundary inputs and decisions.
    data = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    (destination / "records.json.gz").write_bytes(gzip.compress(data, mtime=0))
    (destination / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8")
    (destination / "RESULTS.md").write_text(render_report(summary), encoding="utf-8")


def render_report(summary):
    cases = summary["cases"]
    rows = [
        "# Supply dispute experiment",
        "",
        "Both target runs admitted 45 primary units and 20 supplemental units for the same beneficiary. "
        "They used identical local observations and active specifications. The warm target reused the graph "
        "published after the source paid 60 + 30. The exclusion kept that graph available and prevented payment.",
        "",
        "| Case | New partial graphs expanded | Complete plans tested in search | Published candidates inspected "
        "| All symbolic checks¹ | All numeric bindings¹ | Outcome |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for label, case in cases.items():
        m = case["target_plan"]["metrics"]
        h = case["helper_calls_in_target_plan_and_settlement"]
        outcome = "45 + 20" if case["settlement_status"] == ADMITTED else "payment refused"
        rows.append(f"| {label} | {m['expansions']} | {m['tested']} | {m['inspected']} "
                    f"| {h['proof_error']} | {h['bind_graph']} | {outcome} |")
    source = cases["warm"]["source_plan"]["metrics"]
    t = summary["timing"]
    gov = summary["governance"]
    comp = gov["compensation"]
    rows.extend([
        "",
        "¹ Counted inside the executed ZTES libraries during target plan derivation, plan admission and "
        "settlement. The plan criterion independently rechecks the graph and its binding. Each run also "
        "invoked the plan criterion once and the settlement criterion once in this window. Replay and fault "
        "probes are excluded from the counts.",
        "",
        f"Source construction expanded {source['expansions']} partial graphs and tested {source['tested']} "
        "complete candidates. The four-node graph allocates primary cover, calculates the residual, "
        "allocates supplemental cover and credits the beneficiary. In the version-change control the target "
        "uses a different search order. In the stricter control it requires an additional independent review. "
        "Both obtain a fresh valid graph.",
        "",
        "## Timing",
        "",
        f"{t['pairs']} matched batches in one process, rotating the execution order. Python {summary['python']} "
        f"on {summary['platform']}. Reported values are median milliseconds. Timed runs have "
        "instrumentation disabled. The earlier acceptance runs warm the interpreter.",
        "",
        "| Schedule | A constructs plan | A publishes | B snapshot, plan and settlement | A and B together |",
        "|---|---:|---:|---:|---:|",
    ])
    for mode, m in t["medians"].items():
        rows.append(f"| {mode} | {m['source_plan_ms']:.3f} | {m['publication_ms']:.3f} "
                    f"| {m['target_path_ms']:.3f} | {m['workload_ms']:.3f} |")
    replay = summary["full_replay"]
    compare = summary["comparison"]
    warm = cases["warm"]
    refs = compare["reductions"]
    rows.extend([
        "",
        f"The median paired target saving (cold minus warm) was {t['paired_target_saving_median_ms']:.3f} ms. "
        f"The warm target was faster in {t['pairs_with_lower_warm_target_time']}/{t['pairs']} batches. "
        f"For the whole two-case workload, the median saving (unpublished minus warm) was "
        f"{t['paired_two_case_saving_median_ms']:.3f} ms, with warm faster in "
        f"{t['batches_with_lower_warm_workload_time']}/{t['pairs']} batches. Negative savings mean greater cost. "
        "The two-case comparison charges publication to the warm run. It includes boundary inputs and judgments, "
        "and excludes initialization, replay, controls and file I/O. Fresh search also builds and records a "
        "longer derivation trace. Timings include that serialization and hashing work. These local timings "
        "describe this fixture.",
        "",
        "## One publication across several targets",
        "",
        "Each batch compares a source that publishes once with a source that never publishes. Both then process "
        "the same eight distinct cold-chain cases, with their own parties, contracts and amounts. Each row "
        "measures the whole workload from the first source observation through the stated target, including "
        "publication when enabled. The three rows are cumulative observations of the same runs.",
        "",
        "| Targets after A | Complete fresh plans without / with publication | Median ms without publication "
        "| Median ms with publication | Median paired saving (ms) | Faster with publication |",
        "|---:|---:|---:|---:|---:|---:|",
    ])
    for n, row in summary["series"]["sizes"].items():
        c, w = row["cold"], row["warm"]
        rows.append(f"| {n} | {c['metrics']['tested']} / {w['metrics']['tested']} | {c['median_ms']:.3f} "
                    f"| {w['median_ms']:.3f} | {row['paired_median_saving_ms']:.3f} "
                    f"| {row['pairs_with_lower_warm_total']}/{len(w['samples_ms'])} |")
    rows.extend([
        "",
        "## Causal checks",
        "",
        f"- In the warm record, transport diagnosis {refs['transport']['diagnosis_event']} cites base event "
        f"{refs['transport']['base_event']}. Cold-chain diagnosis {refs['cold_chain']['diagnosis_event']} "
        f"cites base event {refs['cold_chain']['base_event']}. Their projected signatures agree. Each "
        "specialized diagnosis remained pending on the separate funding-only control.",
        f"- Target settlement {compare['tampered_event']} uses publication `{warm['publication']['ref']}`. "
        "Changing its reference in a copy caused full replay to reject precisely that event. "
        "A duplicate submission and a dangling reference were also refused by the local settlement criterion.",
        f"- Governance event {gov['transition']['trigger_event']} activated new specification versions under "
        f"prior authority. The fixed-regime certificate bounds cover at {gov['obstruction']['certificate']['max_total']} "
        f"for a loss of {gov['obstruction']['certificate']['fixed_loss']}. The funded new regime paid 60 + 30. "
        "The waiting control has a continuation paying 90 under the original regime.",
        f"- The coverage criterion refused premature closure. Event {comp['closure_event']} closed compensation "
        "after the carrier's refund of 2 and the supplier's refund of 7.",
        "",
        f"Full replay from genesis passed on all {len(replay)} exported records, including the valid prefix with "
        "incomplete compensation. Entries for the fixed, incomplete and completed governance runs include "
        "shared prefixes. Rejected attempts are reported separately from ledger events.",
        "",
        "| Record | Admitted events including specifications and genesis | Full replay (ms, single run) |",
        "|---|---:|---:|",
    ])
    rows.extend(f"| {name} | {data['events']} | {data['full_replay_ms']:.3f} |" for name, data in replay.items())
    rows.extend(["", "Raw evidence and per-batch samples are in [results.json](results.json). "
                 "The [record archive](records.json.gz) includes the executable specifications.", ""])
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build") / "structural-memoization",
                        help="directory for the new report and records")
    parser.add_argument("--pairs", type=int, default=60, help="matched batches for the single-target timing")
    parser.add_argument("--series-pairs", type=int, default=24, help="matched batches for the 1/4/8 target series")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--verify", type=Path, metavar="RECORDS.JSON.GZ", help="replay a saved archive only")
    action.add_argument("--export-systems", type=Path, metavar="DIR", help="write native ZTES system directories")
    args = parser.parse_args()
    if args.export_systems:
        export_systems(args.export_systems)
        print(f"Exported and checked two native ZTES systems in {args.export_systems}")
        return
    if args.verify:
        with gzip.open(args.verify, "rt", encoding="utf-8") as bundle:
            for name, record in json.load(bundle).items():
                audit = full_replay(record)
                print(f"{name}: {audit['events']} events, full replay OK")
        return
    if args.pairs < 1 or args.series_pairs < 1:
        parser.error("the timing sample counts must be positive")
    from governance import run_governance
    from amortization import run_amortization

    cases, records = {}, {}
    for mode in ("cold", "warm", "exclusion", "stricter", "version_change", "unpublished"):
        cases[mode], records[mode], _ = run_case(mode)
    comparison = check_comparison(cases, records)
    comparison["refinement_witnesses"], records["funding_only"] = refinement_witnesses()
    governance, additional_records = run_governance()
    require(not (set(records) & set(additional_records)), "record name collision")
    records.update(additional_records)
    timing = benchmark(args.pairs)
    series, series_records = run_amortization(args.series_pairs)
    require(not (set(records) & set(series_records)), "series record name collision")
    records.update(series_records)
    replay = {name: full_replay(record) for name, record in records.items()}
    summary = {"python": platform.python_version(), "platform": platform.platform(),
               "cases": cases, "comparison": comparison, "governance": governance,
               "full_replay": replay, "timing": timing, "series": series}
    write_results(args.output, summary, records)
    for name, case in cases.items():
        print(name, case["settlement_status"], case["target_plan"]["metrics"])
    print(f"Full replay verified {len(replay)} records. Results in {args.output}")


if __name__ == "__main__":
    main()
