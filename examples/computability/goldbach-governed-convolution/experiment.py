"""Run and replay finite ordered-prime convolutions with a governed right operand."""

import argparse
from copy import deepcopy
import gzip
import json
from math import isqrt
from pathlib import Path
import sys

from ztes.model import judge, realize
from ztes.model.view import Record
from ztes.service import AbstractionService
from ztes.substrate import ADMITTED, NOT_YET, MemoryStore, Z0, events, lookups
from ztes.substrate.replay import verify


MODES = ("unchanged", "governed_reuse", "governed_fresh", "no_trigger")
HORIZON = 20
CAP = 13


def require(condition, message):
    if not condition:
        raise ValueError(message)


def admitted(executor, name, occurrence=None):
    status, value = executor.execute(name, occurrence)
    require(status == ADMITTED, f"{name} at prefix {executor.position}: {status}, {value}")


def query(executor, number, total, policy):
    admitted(executor, "query", {"id": number, "total": total, "policy": policy})
    # At most one transform for each operand of the current product.
    for _ in range(3):
        status, _ = executor.execute("spectrum")
        if status == NOT_YET:
            break
        require(status == ADMITTED, f"unexpected spectrum outcome {status}")
    else:
        raise ValueError("the query generated more than two transforms")
    admitted(executor, "product")
    admitted(executor, "answer")


def observe_inapplicable_change(executor):
    prefix = list(executor.prefix())
    status, _ = executor.execute("activate")
    require(status == NOT_YET and list(executor.prefix()) == prefix, "inapplicable change admitted")
    return {"lineage": "activate", "prefix_length": len(prefix), "tip": events.link(prefix),
            "outcome": status, "events_added": 0}


def observe_admissible_change(record):
    """At the end of a record: the change the activation ontology proposes, and the verdict of the
    active criterion on it. Nothing is appended."""
    prefix = Record.of(record)
    candidate = realize(prefix, lookups.load(prefix, lookups.active(prefix, "activate", "ontology")))
    require(candidate is not None, "no change proposed at the end of the record")
    verdict = judge(prefix, lookups.load(prefix, lookups.active(prefix, "activate", "criterion")), candidate)
    require(verdict is True, "the proposed change is not admissible")
    return {"lineage": "activate", "prefix_length": len(record), "tip": events.link(record),
            "answer_ref": candidate["answer_ref"], "admissible": verdict, "events_added": 0}


def run_fixture(mode):
    from model import system

    require(mode in MODES, f"unknown experiment {mode}")
    spec = system()
    require(not spec.check(log=lambda _: None), "native static checks failed")
    executor = spec.run(MemoryStore(), plan=[{"phase": 1}, {"phase": 2}], log=lambda _: None)
    admitted(executor, "catalog", HORIZON)
    admitted(executor, "left")
    admitted(executor, "right")
    query(executor, 1, 4 if mode == "no_trigger" else 20, "reuse")
    observed = None
    if mode in ("governed_reuse", "governed_fresh"):
        admitted(executor, "activate")
        admitted(executor, "right")
    elif mode == "no_trigger":
        observed = observe_inapplicable_change(executor)
    query(executor, 2, 20, "fresh" if mode == "governed_fresh" else "reuse")
    return list(executor.prefix()), observed


def select(record, lineage):
    return [e for e in record if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == lineage]


def fork_executor(record):
    store = MemoryStore()
    for i, event in enumerate(record):
        require(event["coord"]["n"] == i and store.put_if_absent(i, event), "invalid source prefix")
    names = {e["coord"]["abstraction"] for e in record if e["coord"]["kind"] == "spec"}
    return Z0(store, {name: AbstractionService(store, name) for name in names})


def arithmetic_grid(left_bound, right_bound, width):
    """Independent enumeration using the stated domain and no recorded factor or transform."""
    left = [p for p in range(2, left_bound + 1)
            if all(p % d for d in range(2, isqrt(p) + 1))]
    right = [q for q in left if q <= right_bound]
    pairs = [[] for _ in range(width)]
    for p in left:
        for q in right:
            pairs[p + q].append([p, q])
    return pairs


def generator_calls(record, event):
    """Count actual library transform calls while re-deriving this admitted candidate."""
    i = event["coord"]["n"]
    prefix = Record.of(record[:i])
    ontology = lookups.load(prefix, event["coord"]["ontology"])
    calls = []

    def observe(frame, kind, arg):
        if kind == "call" and frame.f_code.co_filename == "<library>" and frame.f_code.co_name == "transform":
            calls.append("inverse" if frame.f_locals["inverse"] else "forward")

    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        candidate = realize(prefix, ontology)
    finally:
        sys.setprofile(previous)
    require(candidate == event["payload"], f"re-derived payload differs at {i}")
    return calls


def govern_trace(record, changed):
    changes = select(record, "activate")
    require(len(changes) == int(changed), "wrong number of changes")
    if not changed:
        return None
    event, = changes
    c, w = event["coord"], event["payload"]
    i = c["n"]
    require(w["answer_ref"] == "answer/1" and w["old_right_ref"] == "right/1" and w["cap"] == CAP,
            "change does not resolve to the original right snapshot and answer")
    require(select(record, "answer")[0]["coord"]["n"] < i < select(record, "right")[1]["coord"]["n"],
            "change out of causal order")
    require(c["criterion"] == lookups.active(record[:i], "activate", "criterion"),
            "change was not judged by the preceding authority")
    carried = {s["role"]: s for s in c["carries"]["specs"]}
    require(set(carried) == {"ontology", "criterion"}, "wrong versions carried")
    old, new = {}, {}
    for role, spec in carried.items():
        old[role] = lookups.active(record[:i], "right", role)
        new[role] = lookups.active(record[:i+1], "right", role)
        require(spec["abstraction"] == "right" and old[role] != new[role] == spec["addr"],
                "right version transition is inconsistent")
        for role_holder in ("left", "answer"):
            require(lookups.active(record[:i], role_holder, role) == lookups.active(record[:i+1], role_holder, role),
                    f"{role_holder} authority changed")
    return {"position": i, "prior_authority": c["criterion"], "old_right_versions": old,
            "new_right_versions": new, "prior_answer": w["answer_ref"], "old_right_ref": w["old_right_ref"]}


def audit_run(mode, record):
    for judgment_only in (True, False):
        errors = verify(record, judgments_only=judgment_only)
        require(not errors, (mode, "judgments_only" if judgment_only else "full", errors[:1]))
    changed = mode.startswith("governed_")
    governance = govern_trace(record, changed)
    catalog, = select(record, "catalog")
    require(catalog["payload"] == HORIZON, "wrong catalogue horizon")
    inputs = select(record, "query")
    spectra = {e["payload"]["ref"]: e for e in select(record, "spectrum")}
    require(len(spectra) == len(select(record, "spectrum")), "ambiguous spectrum reference")
    sources = {e["payload"]["ref"]: e for lineage in ("left", "right") for e in select(record, lineage)}
    products, answers = select(record, "product"), select(record, "answer")
    require(len(inputs) == len(products) == len(answers) == 2, "expected two complete queries")
    reports = []
    for k, (request, product, answer) in enumerate(zip(inputs, products, answers), start=1):
        r, p, a = request["payload"], product["payload"], answer["payload"]
        qi, pi, ai = (e["coord"]["n"] for e in (request, product, answer))
        total = 4 if mode == "no_trigger" and k == 1 else 20
        right_bound = CAP if changed and k == 2 else HORIZON
        require(qi < pi < ai and r["id"] == p["query_id"] == a["query_id"] == k, "query order or identity")
        require(r["total"] == a["total"] == total and a["product_ref"] == p["ref"], "answer provenance")
        basis = arithmetic_grid(HORIZON, right_bound, 64)
        counts = [len(row) for row in basis]
        require(p["counts"] == counts, f"all-coefficient oracle disagrees at {mode} query {k}")
        require(a["pairs"] == basis[total] and a["count"] == counts[total], "ordered witnesses disagree")
        positions = {"query": qi, "product": pi, "answer": ai}
        reused = []
        forwards = 0
        spectrum_check_terms = 0
        for side in ("left", "right"):
            ref = p[side + "_ref"]
            source = sources[ref]
            spectrum = spectra[p[side + "_spectrum"]]
            s = spectrum["payload"]
            si = spectrum["coord"]["n"]
            expected_ref = "right/2" if side == "right" and changed and k == 2 else side + "/1"
            require(ref == expected_ref == s["source_ref"] and s["side"] == side, "wrong source reference")
            require(source["coord"]["n"] < si < pi and (s["length"], s["modulus"], s["root"]) == (64, 257, 3),
                    "spectrum position or parameters do not match")
            positions[side + "_snapshot"] = source["coord"]["n"]
            positions[side + "_spectrum"] = si
            if si < qi:
                reused.append(side)
            else:
                require(s["query_id"] == k and generator_calls(record, spectrum) == ["forward"],
                        "spectrum did not perform one forward transform")
                forwards += 1
                # The spectrum criterion directly evaluates one monomial per source prime at each root.
                spectrum_check_terms += s["length"] * len(source["payload"]["primes"])
        require(generator_calls(record, product) == ["inverse"], "product did not perform one inverse transform")
        expected_reuse = ([] if k == 1 or mode == "governed_fresh" else
                          ["left"] if changed else ["left", "right"])
        require(reused == expected_reuse, f"wrong reusable evidence at {mode} query {k}")
        reports.append({"id": k, "total": total, "count": a["count"], "pairs": a["pairs"],
                        "left_ref": p["left_ref"], "right_ref": p["right_ref"],
                        "left_spectrum": p["left_spectrum"], "right_spectrum": p["right_spectrum"],
                        "reused_sides": reused, "generator_forwards": forwards, "generator_inverses": 1,
                        "spectrum_criterion_monomial_terms": spectrum_check_terms,
                        "product_criterion_pair_enumerations": sum(counts),
                        "coefficients_checked": len(counts), "ordered_pairs_in_grid": sum(counts),
                        "attainable_totals": sum(n > 0 for n in counts),
                        "positions": positions, "answer_criterion": answer["coord"]["criterion"]})
    require(reports[0]["answer_criterion"] == reports[1]["answer_criterion"], "changed answer criterion")
    result = {"queries": reports, "governance": governance,
              "replay": {"events": len(record), "judgments_verified": len(record),
                         "fully_verified": len(record), "tip": events.link(record)}}
    if mode == "no_trigger":
        cut = inputs[1]["coord"]["n"]
        result["activation_attempt"] = observe_inapplicable_change(fork_executor(record[:cut]))
        # Once the answer for 20 exhibits (3,17), the change is admissible: evidence, not the schedule,
        # decides it. The record ends before the change is invoked.
        result["activation_after_evidence"] = observe_admissible_change(record)
    return result


def reject_at(record, position, fields):
    """Keep the hash link to the real predecessor, and change just the candidate being judged."""
    prefix = list(record[:position+1])
    prefix[-1] = deepcopy(prefix[-1])
    prefix[-1]["payload"].update(fields)
    for judgment_only in (True, False):
        errors = verify(prefix, judgments_only=judgment_only)
        require(len(errors) == 1 and errors[0][0] == position, f"fault not localized at {position}")
        if judgment_only:
            reason = errors[0][1]
            require("criterion is false" in reason, f"fault escaped the local criterion: {reason}")
    return {"position": position, "replacement_fields": fields, "judgment_error": reason}


def audit(records):
    require(set(records) == set(MODES), "missing or unknown archived execution")
    runs = {mode: audit_run(mode, records[mode]) for mode in MODES}
    warm = records["governed_reuse"]
    first_decision = runs["governed_reuse"]["governance"]["position"]
    second_query = runs["governed_reuse"]["queries"][1]["positions"]["query"]
    require(warm[:first_decision] == records["unchanged"][:first_decision], "nonactivation control mismatch")
    require(warm[:second_query] == records["governed_fresh"][:second_query], "fresh control mismatch")
    before, after = runs["governed_reuse"]["queries"]
    old_counts, new_counts = [event["payload"]["counts"] for event in select(warm, "product")]
    report = {
        "runs": runs,
        "shared_prefixes": {"unchanged_and_governed": first_decision, "fresh_and_reuse": second_query},
        "effect_of_right_restriction": {
            "totals_with_changed_counts": [s for s in range(2 * HORIZON + 1) if old_counts[s] != new_counts[s]],
            "totals_losing_all_witnesses": [s for s in range(2 * HORIZON + 1) if old_counts[s] and not new_counts[s]],
            "ordered_pairs_removed": sum(old_counts) - sum(new_counts),
        },
        "faults": {
            "stale_right_spectrum": reject_at(warm, after["positions"]["product"],
                                               {"right_spectrum": before["right_spectrum"]}),
            "revoked_ordered_witness": reject_at(warm, after["positions"]["answer"],
                                                 {"count": before["count"], "pairs": before["pairs"]}),
            "incomplete_valid_witnesses": reject_at(warm, after["positions"]["answer"],
                                                   {"count": after["count"] - 1, "pairs": after["pairs"][:-1]}),
        },
    }
    return report


def save(destination, records, summary):
    destination.mkdir(parents=True, exist_ok=True)
    data = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with (destination / "records.json.gz").open("wb") as stream:
        with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as zipped:
            zipped.write(data)
    (destination / "results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--output", type=Path, metavar="DIR", help="regenerate and save the four runs")
    action.add_argument("--verify", type=Path, metavar="RECORDS.JSON.GZ", help="audit an archived set of records")
    args = parser.parse_args()
    if args.verify:
        with gzip.open(args.verify, "rt", encoding="utf-8") as archive:
            records = json.load(archive)
        summary = audit(records)
        sidecar = args.verify.with_name("results.json")
        if sidecar.is_file():
            require(summary == json.loads(sidecar.read_text(encoding="utf-8")), "results differ from the archive")
    else:
        fixtures = {mode: run_fixture(mode) for mode in MODES}
        records = {mode: pair[0] for mode, pair in fixtures.items()}
        summary = audit(records)
        require(summary["runs"]["no_trigger"]["activation_attempt"] == fixtures["no_trigger"][1],
                "the no-trigger invocation outcome changed on reconstruction")
        if args.output:
            save(args.output, records, summary)
    for mode, run in summary["runs"].items():
        first, second = run["queries"]
        print(f"{mode}: s={first['total']} has {first['count']} ordered pairs, "
              f"s={second['total']} has {second['count']}; "
              f"{second['generator_forwards']} forward transform(s) for the second query; "
              f"{run['replay']['fully_verified']} events replayed.")


if __name__ == "__main__":
    main()
