"""Measure the cost of publishing one plan across a series of independently settled cases."""

from statistics import median
from time import perf_counter_ns

from case_model import fixture_inputs
from runtime import admitted, full_replay, new_executor, require


SIZES = (1, 4, 8)
COUNTERS = ("expansions", "tested", "inspected", "validated", "bindings")


def target_observations(index):
    """Rebind a cold-chain fixture, preserving its evidence rules and structural signature."""
    case = f"shipment-{index:02d}"
    d, s = 60 + 3 * index, 42 + index
    g = d - s + 8
    result = fixture_inputs("B")
    for lineage, item in result:
        item["case"] = case
        if lineage in ("funding", "policy"):
            item.update(ref=f"{lineage}/{case}", contract=f"order/{case}",
                        beneficiary=f"buyer/{case}", guarantor=f"guarantor/{case}",
                        instrument=f"instrument/{case}")
        if lineage == "funding":
            item.update(lot=f"lot/{case}", primary_payer=f"carrier/{case}", obligation=d,
                        primary_limit=s, guarantee_limit=g)
        elif lineage == "policy":
            item.update(primary_available=s, guarantee_available=g)
        else:
            item.update(lot=f"lot/{case}", ref=f"{case}/{item['kind']}")
            if item["kind"] in ("temperature", "calibration"):
                item["sensor"] = f"device/{case}"
            elif item["kind"] == "quality":
                item["value"] = d
    return result


def settle_case(executor, occurrences, diagnostic_lineage):
    for lineage, boundary in occurrences:
        admitted(executor, lineage, boundary)
    admitted(executor, "base")
    diagnosis = admitted(executor, diagnostic_lineage)
    snapshot = admitted(executor, "snapshot")
    plan = admitted(executor, "plan")
    payment = admitted(executor, "settle")
    return diagnosis, snapshot, plan, payment


def workload(publish, source, fixtures):
    executor = new_executor()
    checkpoints, outcomes = {}, []
    start = perf_counter_ns()
    source_diag, _, source_plan, source_payment = settle_case(executor, source, "transport")
    publication = admitted(executor, "catalogue") if publish else None
    for index, observations in enumerate(fixtures, 1):
        outcomes.append(settle_case(executor, observations, "cold_chain"))
        if index in SIZES:
            checkpoints[index] = (perf_counter_ns() - start) / 1_000_000

    # Assertions, metrics aggregation and replay are outside every timed prefix.
    require(source_plan["origin"] == "fresh" and source_plan["metrics"]["expansions"] > 0,
            "source solved without constructing its plan")
    require((source_payment["primary"], source_payment["supplemental"]) == (60, 30), "source amount")
    if publish:
        require(publication["plan_ref"] == source_plan["ref"] and publication["graph"] == source_plan["graph"],
                "publication does not preserve the source derivation")
    counters = dict.fromkeys(COUNTERS, 0)
    totals = {}
    for index, ((diag, snap, plan, payment), observations) in enumerate(zip(outcomes, fixtures), 1):
        terms = observations[0][1]
        d, s = terms["obligation"], terms["primary_limit"]
        require((payment["case"], payment["contract"], payment["beneficiary"], payment["primary"],
                 payment["supplemental"], payment["credit"]) ==
                (terms["case"], terms["contract"], terms["beneficiary"], s, d - s, d),
                ("unexpected local settlement", index, payment))
        require(diag["signature"] == source_diag["signature"] and len(diag["evidence"]) == 3
                and diag["evidence"] == payment["evidence"], ("diagnostic evidence", index))
        require(plan["graph"] == source_plan["graph"] and plan["versions"] == source_plan["versions"],
                ("target plan", index))
        ref = publication["ordinal"] if publish else 0
        require(plan["publication"] == payment["publication"] == ref
                and plan["origin"] == ("reuse" if publish else "fresh")
                and snap["visible"] == ([ref] if publish else []), ("incorrect provenance", index))
        metrics = plan["metrics"]
        require((metrics["expansions"] == metrics["tested"] == 0 and metrics["validated"] == 1)
                if publish else (metrics["expansions"] > 0 and metrics["tested"] > 0),
                ("unexpected search work", index, metrics))
        for key in COUNTERS:
            counters[key] += metrics[key]
        if index in SIZES:
            totals[index] = dict(counters)

    record = list(executor.prefix())
    actual = [(event["coord"]["abstraction"], event["payload"]) for event in record
              if event["coord"]["kind"] == "exec"]
    require([pair for pair in actual if pair[0] in ("funding", "policy", "evidence")] ==
            [*source, *(pair for fixture in fixtures for pair in fixture)], "recorded observations differ")
    require([payload for lineage, payload in actual if lineage == "catalogue"] ==
            ([publication] if publish else []), "unexpected extra publication")
    return checkpoints, totals, record


def run_amortization(repeats):
    """Return per-prefix paired timings and the two complete eight-target records."""
    if repeats < 1:
        raise ValueError("at least one measured pair is required")
    source = fixture_inputs("A")
    fixtures = [target_observations(i) for i in range(1, max(SIZES) + 1)]
    samples = {n: {"cold": [], "warm": []} for n in SIZES}
    counters = {}
    records = {}
    # One unmeasured pair before alternating the order of the measured pairs.
    workload(False, source, fixtures)
    workload(True, source, fixtures)
    for pair in range(repeats):
        for mode in (("cold", "warm") if pair % 2 == 0 else ("warm", "cold")):
            elapsed, totals, record = workload(mode == "warm", source, fixtures)
            if pair == 0:
                counters[mode] = totals
                records[f"series_{mode}_8"] = record
            else:
                require(counters[mode] == totals, ("work counts changed", mode, pair))
            for n in SIZES:
                samples[n][mode].append(elapsed[n])
    sizes = {}
    for n, modes in samples.items():
        saving = [c - w for c, w in zip(modes["cold"], modes["warm"])]
        by_mode = {mode: {"median_ms": median(values), "samples_ms": values,
                          "metrics": counters[mode][n]} for mode, values in modes.items()}
        sizes[str(n)] = {**by_mode, "paired_median_saving_ms": median(saving),
                         "pairs_with_lower_warm_total": sum(s > 0 for s in saving),
                         "paired_savings_ms": saving}
    replay = {name: full_replay(record) for name, record in records.items()}
    return {"repeats": repeats, "targets": list(SIZES), "clock": "perf_counter_ns", "unit": "ms",
            "window": "First source observation through target settlement, inclusive; one publication only in warm.",
            "sizes": sizes, "full_replay": replay}, records
