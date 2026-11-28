"""Run, archive and audit the governed factorization example on the native ZTES executor."""

import argparse
from copy import deepcopy
from functools import lru_cache
import gzip
import json
from pathlib import Path
import sys

from ztes.model import realize
from ztes.model.view import Record
from ztes.service import AbstractionService
from ztes.substrate import ADMITTED, NOT_YET, MemoryStore, Z0, events, lookups
from ztes.substrate.replay import verify


MODES = ("parity", "fresh", "reuse")
SOURCE = 1121
TARGETS = (2929, 1643)
CONTROL_SOURCE = 1457
GOVERNANCE_CALLS = ("diagnosis", "pattern", "activate")


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def admitted(executor, name, occurrence=None):
    status, value = executor.execute(name, occurrence)
    require(status == ADMITTED, f"{name} at position {executor.position}: {status}, {value}")


def compute(executor, n):
    admitted(executor, "target", n)
    for name in ("plan", "probes", "factor"):
        admitted(executor, name)


def initialize(fresh=False):
    from model import system

    system_spec = system(fresh=fresh)
    problems = system_spec.check(log=lambda _: None)
    require(not problems, problems)
    return system_spec.run(MemoryStore(), plan=[{"phase": 1}, {"phase": 2}], log=lambda _: None)


@lru_cache(maxsize=3)
def _source(mode):
    require(mode in MODES, f"unknown mode {mode}")
    executor = initialize(fresh=(mode == "fresh"))
    compute(executor, SOURCE)
    calls = GOVERNANCE_CALLS[:2] if mode == "parity" else GOVERNANCE_CALLS
    for name in calls:
        admitted(executor, name)
    return tuple(executor.prefix())


def source_prefix(mode):
    """A frozen source run up through publication and the chosen intervention."""
    return list(_source(mode))


def fork_executor(prefix):
    """Open a fresh executor over a copy of an archived prefix."""
    store = MemoryStore()
    for n, event in enumerate(prefix):
        require(event["coord"]["n"] == n and store.put_if_absent(n, event), "invalid starting prefix")
    names = {e["coord"]["abstraction"] for e in prefix if e["coord"]["kind"] == "spec"}
    return Z0(store, {name: AbstractionService(store, name) for name in names})


def run_targets(prefix, targets):
    executor = fork_executor(prefix)
    for n in targets:
        compute(executor, n)
    return list(executor.prefix())


def run_fixture(mode, targets=TARGETS):
    return run_targets(source_prefix(mode), targets)


def observe_no_trigger(executor):
    """Observe invocation outcomes separately from admissions at this specific prefix."""
    prefix = list(executor.prefix())
    calls = []
    for name in GOVERNANCE_CALLS:
        outcome, _ = executor.execute(name)
        after = list(executor.prefix())
        require(after == prefix and outcome == NOT_YET, f"unexpected outcome for {name}: {outcome}")
        calls.append({"lineage": name, "outcome": outcome, "events_added": len(after) - len(prefix)})
    return {"prefix_events": len(prefix), "prefix_tip": events.link(prefix), "calls": calls}


def run_no_trigger():
    executor = initialize()
    compute(executor, CONTROL_SOURCE)
    attempts = observe_no_trigger(executor)
    compute(executor, TARGETS[0])
    return list(executor.prefix()), attempts


def selected(record, lineage):
    return [e for e in record if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == lineage]


def by_key(record, lineage):
    items = selected(record, lineage)
    keyed = {e["payload"]["n"]: e for e in items}
    require(len(items) == len(keyed), f"repeated {lineage} for one input")
    return keyed


def target_metrics(record):
    """Count admitted search probes. Build/read counts describe target plan materialization only."""
    inputs = selected(record, "target")
    plans, blocks, certificates = (by_key(record, name) for name in ("plan", "probes", "factor"))
    order = [e["payload"] for e in inputs]
    require(len(order) == len(set(order)) and set(order) == plans.keys() == blocks.keys() == certificates.keys(),
            "incomplete or duplicate input/plan/probe/certificate chain")
    rows = []
    for event in inputs:
        n = event["payload"]
        plan, block, certificate = plans[n], blocks[n], certificates[n]
        p, b, f = (e["payload"] for e in (plan, block, certificate))
        indices = [e["coord"]["n"] for e in (event, plan, block, certificate)]
        require(indices == sorted(indices), f"noncausal evidence chain for {n}")
        require(p["target_ref"] == f"target/{n}" and b["plan_ref"] == p["ref"] and f["probes_ref"] == b["ref"],
                f"unresolved factor evidence for {n}")
        require(len(b["centers"]) == len(b["differences"]) and
                all(a*a - n == d for a, d in zip(b["centers"], b["differences"])),
                f"probe block inconsistent for {n}")
        rows.append({"n": n, "path": p["mode"], "probes": b["centers"], "factors": f["factors"],
                     "target_builds": int(p["mode"] == "fresh"), "pattern_reads": int(p["mode"] == "reuse"),
                     "event_positions": dict(zip(("target", "plan", "probes", "factor"), indices)),
                     "plan_ontology": plan["coord"]["ontology"], "factor_criterion": certificate["coord"]["criterion"],
                     "pattern_ref": p["pattern_ref"], "activation_ref": p["activation_ref"]})
    return rows


def rederive_plan(record, index):
    """Count actual mask construction calls in the recorded plan ontology, excluding judgments."""
    prefix = Record.of(record[:index])
    event = record[index]
    ontology = lookups.load(prefix, event["coord"]["ontology"])
    builds = 0

    def observe(frame, kind, arg):
        nonlocal builds
        if kind == "call" and frame.f_code.co_filename == "<library>" and frame.f_code.co_name == "mask_for":
            builds += 1

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        candidate = realize(prefix, ontology)
    finally:
        sys.setprofile(previous)
    require(candidate == event["payload"], f"plan changed during instrumentation at {index}")
    return builds


def audit_trace(record, mode):
    """Resolve the domain's stable references to native event coordinates and governing addresses."""
    rows = target_metrics(record)
    require([r["n"] for r in rows] == [SOURCE, *TARGETS], "unexpected fixture order")
    source = rows[0]
    diagnosis, = selected(record, "diagnosis")
    publication, = selected(record, "pattern")
    d, p = diagnosis["payload"], publication["payload"]
    block = record[source["event_positions"]["probes"]]
    require(block["payload"]["ref"] == d["probes_ref"] and d["ref"] == p["diagnosis_ref"],
            "broken discovery evidence chain")
    require(source["event_positions"]["factor"] < diagnosis["coord"]["n"] < publication["coord"]["n"],
            "discovery references an unavailable predecessor")
    require(d["failed_centers"] == [35, 37] and d["threshold"] == 2, "source failures")
    require((p["modulus"], p["residue"], p["mask"]) == (16, 1, [1, 7, 9, 15]), "published mask")
    changes = selected(record, "activate")
    change_info = None
    if mode == "parity":
        require(not changes, "unrequested governance change")
        require(all(row["path"] == "parity" and not row["pattern_ref"] and not row["activation_ref"]
                    for row in rows), "baseline used a new policy")
    else:
        trigger, = changes
        g = trigger["payload"]
        i = trigger["coord"]["n"]
        carried, = trigger["coord"]["carries"]["specs"]
        previous = lookups.active(record[:i], "plan", "ontology")
        new = lookups.active(record[:i+1], "plan", "ontology")
        require(carried["abstraction"] == "plan" and carried["role"] == "ontology" and
                previous != new == carried["addr"] and previous == source["plan_ontology"], "R1 transition")
        require(trigger["coord"]["criterion"] == lookups.active(record[:i], "activate", "criterion"),
                "old governing authority unavailable")
        require(publication["coord"]["n"] < i < rows[1]["event_positions"]["target"] and
                g["diagnosis_ref"] == d["ref"] and g["pattern_ref"] == p["ref"] and g["materialization"] == mode,
                "governance provenance")
        require(all(row["pattern_ref"] == p["ref"] and row["activation_ref"] == g["ref"] and
                    row["plan_ontology"] == new for row in rows[1:]), "target governance or pattern provenance")
        change_info = {"event": i, "ref": g["ref"], "authority": trigger["coord"]["criterion"],
                       "previous_plan_ontology": previous, "active_plan_ontology": new,
                       "diagnosis_ref": g["diagnosis_ref"], "pattern_ref": g["pattern_ref"]}
    require(len({row["factor_criterion"] for row in rows}) == 1, "factor criterion changed")
    expected_centers = [[35, 37, 39], [55, 57, 59, 61, 63, 65] if mode == "parity" else [55, 57, 63, 65], [42]]
    require([r["probes"] for r in rows] == expected_centers, f"unexpected {mode} probe sequences")
    require([r["factors"] for r in rows] == [[19, 59], [29, 101], [31, 53]], "factor certificates")
    if mode != "parity":
        require([r["path"] for r in rows] == ["parity", mode, "fallback"], "unexpected policy paths")
    for row in rows:
        count = rederive_plan(record, row["event_positions"]["plan"])
        require(count == row["target_builds"], "mask construction incorrectly attributed")
        row["observed_mask_constructions_in_plan_rederivation"] = count
    return {"targets": rows, "search_probes": sum(len(row["probes"]) for row in rows),
            "diagnosis": {"event": diagnosis["coord"]["n"], **d},
            "publication": {"event": publication["coord"]["n"], **p}, "activation": change_info,
            "distinct_factor_criteria": 1}


def tamper(record, index, key, bad_value):
    """End the altered prefix exactly at the challenged event, preserving its predecessor hash."""
    trial = list(record[:index+1])
    trial[-1] = deepcopy(trial[-1])
    trial[-1]["payload"][key] = bad_value
    errors = verify(trial, judgments_only=True)
    require(len(errors) == 1 and errors[0][0] == index and "criterion is false" in errors[0][1],
            ("fault escaped the local criterion", index, key, errors))
    full = verify(trial)
    require(len(full) == 1 and full[0][0] == index, ("fault escaped full replay", index, key, full))
    return {"event": index, "field": key, "injected_value": bad_value, "judgment_error": errors[0][1],
            "full_replay_rejected_at": full[0][0]}


def replay_totals(record, name):
    for judgments_only in (True, False):
        errors = verify(record, judgments_only=judgments_only)
        require(not errors, (name, "judgment" if judgments_only else "full", errors[:1]))
    return {"events": len(record), "judgments_verified": len(record),
            "fully_verified": len(record), "tip": events.link(record)}


def audit_no_trigger(record, reuse_record):
    replay = replay_totals(record, "no_trigger")
    rows = target_metrics(record)
    require([r["n"] for r in rows] == [CONTROL_SOURCE, TARGETS[0]], "unexpected no-trigger inputs")
    source, target = rows
    require(SOURCE % 16 == CONTROL_SOURCE % 16 == 1 and source["probes"] == [39] and
            source["factors"] == [31, 47], "no-trigger source must succeed on the first probe")
    require(target["probes"] == [55, 57, 59, 61, 63, 65] and target["factors"] == [29, 101],
            "no-trigger target search differs from parity")
    initial = source["event_positions"]["target"]
    require(initial == selected(reuse_record, "target")[0]["coord"]["n"] and
            record[:initial] == reuse_record[:initial], "control started under different specifications")
    require(not any(selected(record, name) for name in GOVERNANCE_CALLS), "unexpected governance event")
    require(all(r["path"] == "parity" and not r["activation_ref"] and not r["pattern_ref"] for r in rows)
            and source["plan_ontology"] == target["plan_ontology"]
            and source["factor_criterion"] == target["factor_criterion"], "unexpected control authorities")
    cut = source["event_positions"]["factor"] + 1
    require(cut == target["event_positions"]["target"], "control invocations appended an event")
    attempts = observe_no_trigger(fork_executor(record[:cut]))
    # The target's own failed probes cannot start a diagnosis: the record is terminal for governance.
    after_target = observe_no_trigger(fork_executor(record))
    return {"targets": rows, "identical_initial_events": initial, "attempts": attempts,
            "attempts_after_target": after_target,
            "search_probes": sum(len(r["probes"]) for r in rows), "replay": replay}


def audit_records(records):
    modes = set(MODES)
    require(set(records) in (modes, modes | {"no_trigger"}), "unexpected archive contents")
    result = {}
    for mode in MODES:
        record = records[mode]
        replay = replay_totals(record, mode)
        result[mode] = audit_trace(record, mode)
        result[mode]["replay"] = replay
    activation = result["reuse"]["activation"]["event"]
    require(records["parity"][:activation] == records["reuse"][:activation],
            "paired intervention has different source prefixes")
    require([r["factors"] for r in result["fresh"]["targets"]] == [r["factors"] for r in result["reuse"]["targets"]],
            "materialization controls disagree")
    record = records["reuse"]
    pattern_pos = result["reuse"]["publication"]["event"]
    target_plan_pos = result["reuse"]["targets"][1]["event_positions"]["plan"]
    faults = {"incomplete_mask": tamper(record, pattern_pos, "mask", [7, 15]),
              "dangling_plan_reference": tamper(record, target_plan_pos, "pattern_ref", "pattern/missing"),
              "obsolete_plan_version": {}}
    trial = list(record[:target_plan_pos+1])
    trial[-1] = deepcopy(trial[-1])
    trial[-1]["coord"]["ontology"] = result["reuse"]["activation"]["previous_plan_ontology"]
    errors = verify(trial, judgments_only=True)
    require(len(errors) == 1 and errors[0][0] == target_plan_pos and "version not active" in errors[0][1],
            ("obsolete plan version accepted", errors))
    faults["obsolete_plan_version"] = {"event": target_plan_pos, "judgment_error": errors[0][1]}
    fallback_pos = result["reuse"]["targets"][2]["event_positions"]["plan"]
    trial = list(record[:fallback_pos+1])
    trial[-1] = deepcopy(trial[-1])
    trial[-1]["payload"]["mode"] = "reuse"
    trial[-1]["payload"]["mask"] = result["reuse"]["publication"]["mask"]
    errors = verify(trial, judgments_only=True)
    full = verify(trial)
    require(len(errors) == 1 and errors[0][0] == fallback_pos and "criterion is false" in errors[0][1]
            and len(full) == 1 and full[0][0] == fallback_pos, ("wrong signature accepted", errors, full))
    faults["wrong_signature"] = {"event": fallback_pos, "field": "mode, mask",
                                 "injected_value": ["reuse", result["reuse"]["publication"]["mask"]],
                                 "judgment_error": errors[0][1], "full_replay_rejected_at": full[0][0]}
    summary = {"runs": result, "identical_source_prefix_events": activation, "faults": faults}
    if "no_trigger" in records:
        summary["no_trigger"] = audit_no_trigger(records["no_trigger"], records["reuse"])
    return summary


def load_archive(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def write_results(destination, records, summary):
    destination.mkdir(exist_ok=True, parents=True)
    archive = destination / "records.json.gz"
    data = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with archive.open("wb") as output:
        with gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=0) as compressed:
            compressed.write(data)
    (destination / "results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--verify", type=Path, metavar="RECORDS.JSON.GZ",
                        help="replay the archive and recheck any no-trigger calls at their recorded prefix")
    action.add_argument("--output", type=Path, default=Path(__file__).with_name("results"),
                        help="destination for regenerated records and KPI results")
    args = parser.parse_args()
    if args.verify:
        summary = audit_records(load_archive(args.verify))
        sidecar = args.verify.with_name("results.json")
        if sidecar.is_file():
            saved = json.loads(sidecar.read_text(encoding="utf-8"))
            require(("no_trigger" in saved) == ("no_trigger" in summary),
                    "archive and results disagree on the presence of the no-trigger control")
            if "no_trigger" in summary:
                for key in ("attempts", "attempts_after_target"):
                    require(saved["no_trigger"].get(key) == summary["no_trigger"][key],
                            "archived no-trigger invocation log differs")
    else:
        records = {mode: run_fixture(mode) for mode in MODES}
        records["no_trigger"], observed = run_no_trigger()
        summary = audit_records(records)
        require(observed == summary["no_trigger"]["attempts"], "no-trigger outcomes changed on reconstruction")
        write_results(args.output, records, summary)
    for name, run in summary["runs"].items():
        print(f"{name}: {run['search_probes']} search probes, {run['replay']['events']} events verified")
    print(f"Paired runs have {summary['identical_source_prefix_events']} identical events before activation.")
    if "no_trigger" in summary:
        control = summary["no_trigger"]
        print(f"No-trigger control: {len(control['attempts']['calls'])} calls appended zero events; "
              f"{control['replay']['events']} events verified.")
    else:
        print("Legacy archive: verified the three original runs.")
    print(f"All {len(summary['faults'])} injected faults were rejected at the affected event.")


if __name__ == "__main__":
    main()
