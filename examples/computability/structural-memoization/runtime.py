"""Shared construction and observation of native ZTES executions."""

from functools import cache
from time import perf_counter_ns

from ztes.service import AbstractionService
from ztes.substrate import ADMITTED, MemoryStore, Z0, events
from ztes.substrate.replay import verify


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


@cache
def initial_specifications():
    from case_model import specifications

    return specifications()


def new_executor():
    pairs = initial_specifications()
    store = MemoryStore()
    services = {c["abstraction"]: AbstractionService(store, c["abstraction"]) for c, _ in pairs}
    executor = Z0(store, services)
    for criterion, _ in pairs:
        require(executor.admit_criterion(criterion) == ADMITTED, criterion["abstraction"])
    for _, ontology in pairs:
        require(executor.admit_ontology(ontology) == ADMITTED, ontology["abstraction"])
    return executor


def admitted(executor, lineage, payload=None):
    status, value = executor.execute(lineage, payload)
    require(status == ADMITTED, f"{lineage} at prefix {executor.position}: {status}, {value}")
    return value


def timed(action, *args):
    start = perf_counter_ns()
    result = action(*args)
    return result, (perf_counter_ns() - start) / 1_000_000


def full_replay(record):
    errors, elapsed = timed(verify, record)
    require(not errors, f"full replay failed: {errors[:1]}")
    return {"events": len(record), "full_replay_ms": elapsed, "errors": len(errors),
            "tip": events.link(record)}
