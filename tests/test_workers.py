"""Phase 3 by workers: one instance of Z₀ per abstraction on one shared record (system/workers.py).

The order of invocations is then decided by a race. What must hold under every schedule: the
record replays (R2), every abstraction ends in the same state, and what a system states in
"expect" (or in its "any_schedule" part, where a result is resolved against the context) holds.
"""
import random
import time

import fakeredis
import pytest

from conftest import ROOT, SQRT2, make_system, quiet
from ztes.service import AbstractionService, ServiceUnavailable
from ztes.substrate.replay import verify
from ztes.substrate.store import DiskStore, MemoryStore, RedisStore, read
from ztes.substrate.z0 import ADMITTED, Z0
from ztes.system import workers
from ztes.system.report import check_expect
from ztes.system.system import System

EXAMPLES = sorted(p.name for p in (ROOT / "examples").iterdir() if (p / "system.json").exists())
STORES = {"memory": lambda tmp: MemoryStore(), "disk": lambda tmp: DiskStore(tmp),
          "redis": lambda tmp: RedisStore(client=fakeredis.FakeRedis(), batch=5)}


def histories(C):
    out = {}
    for e in C:
        if e["coord"]["kind"] == "exec":
            out.setdefault(e["coord"]["abstraction"], []).append(e["payload"])
    return out


def by_agenda(name):
    system, store = System(ROOT / "examples" / name), MemoryStore()
    system.run(store, log=quiet)
    return system, read(store)


def holds_under_any_schedule(system, C, central):
    assert verify(list(C)) == []                                    # R2
    assert check_expect(system, C, log=quiet, any_schedule=True) == []
    assert system.states(C) == central[0].states(central[1])        # every abstraction ends the same way
    for row in histories(C).get("profile", [[]])[-1]:               # the recorded counts are consistent
        assert row["I"] == row["A"] + row["U"] + row["F"] and 0 <= row["H"] <= row["U"]


@pytest.mark.parametrize("backend", STORES)
@pytest.mark.parametrize("name", EXAMPLES)
def test_every_example_by_workers_on_every_store(name, backend, tmp_path):
    system, store = System(ROOT / "examples" / name), STORES[backend](tmp_path)
    workers.run(system, store, log=quiet)
    holds_under_any_schedule(system, read(store), by_agenda(name))


@pytest.mark.parametrize("name", EXAMPLES)
def test_every_example_under_random_schedules(name):
    """Each worker pauses at random before every invocation, so the race is decided differently each time."""
    central = by_agenda(name)
    for seed in range(4):
        rnd = random.Random(seed)
        system, store = System(ROOT / "examples" / name), MemoryStore()
        workers.run(system, store, log=quiet, hesitate=lambda: time.sleep(rnd.random() * 0.003))
        holds_under_any_schedule(system, read(store), central)


def test_determined_results_do_not_depend_on_the_schedule():
    """Theorem K, executed: other orders of the record, the same history of every abstraction."""
    _, central = by_agenda("dedekind-cut")
    orders = set()
    for seed in range(6):
        rnd = random.Random(seed)
        system, store = System(ROOT / "examples" / "dedekind-cut"), MemoryStore()
        workers.run(system, store, log=quiet, hesitate=lambda: time.sleep(rnd.random() * 0.003))
        C = read(store)
        mine, theirs = histories(C), histories(central)
        assert {a: h for a, h in mine.items() if a != "profile"} == {a: h for a, h in theirs.items() if a != "profile"}
        orders.add(tuple(e["coord"].get("abstraction") for e in C))
    assert tuple(e["coord"].get("abstraction") for e in central) not in orders or len(orders) > 1


def test_a_resolution_against_the_context_may_take_another_valid_course():
    """D1: goldbach admits the witness it finds among the primes recorded when it is invoked."""
    _, central = by_agenda("prime-witnesses")
    system, store = System(ROOT / "examples" / "prime-witnesses"), MemoryStore()
    workers.run(system, store, log=quiet)
    got, expected = histories(read(store)), histories(central)
    assert got["primes"] == expected["primes"] and got["twins"] == expected["twins"]
    assert [w["even"] for w in got["goldbach"]] == [w["even"] for w in expected["goldbach"]]
    assert all(w["p"] + w["q"] == w["even"] and {w["p"], w["q"]} <= set(got["primes"]) for w in got["goldbach"])


def test_waiting_for_the_complete_horizon_makes_the_answer_independent_of_the_schedule():
    """The same example, two designs. ontology.v1 of goldbach answers with the primes visible when it
    is invoked; ontology.v2 waits until every prime that could take part is recorded."""
    path = ROOT / "examples" / "prime-witnesses"
    v2 = [{"phase": 1}, {"phase": 2}, {"govern": ["goldbach/ontology.v2"]}, {"phase": 3}]
    always = [{"even": 10, "p": 3, "q": 7}, {"even": 14, "p": 3, "q": 11}, {"even": 20, "p": 3, "q": 17}]
    store = MemoryStore()
    System(path).run(store, log=quiet, plan=v2)
    assert histories(read(store))["goldbach"] == always                # under the agenda
    seen_v1 = set()
    for seed in range(6):
        rnd = random.Random(seed)
        pause = lambda: time.sleep(rnd.random() * 0.003)
        store = MemoryStore()
        workers.run(System(path), store, log=quiet, plan=v2, hesitate=pause)
        assert histories(read(store))["goldbach"] == always and verify(list(read(store))) == []
        store = MemoryStore()
        workers.run(System(path), store, log=quiet, hesitate=pause)     # the plan of the example: v1
        seen_v1.add(str(histories(read(store))["goldbach"]))
    _, central = by_agenda("prime-witnesses")
    assert seen_v1 != {str(histories(central)["goldbach"])}            # v1: another valid course was taken


# ---- Z₀: a judgment stands while its horizon stands (Lemma 6) ----

class Counting(AbstractionService):
    realized = 0

    def realize(self, address, n, occurrence=None):
        self.realized += 1
        return super().realize(address, n, occurrence)


class Overtaken:
    """A store on which another instance of Z₀ appends just before our first append."""

    def __init__(self, store, other):
        self.store, self.other = store, other

    def get(self, n):
        return self.store.get(n)

    def put_if_absent(self, n, event):
        if self.other:
            other, self.other = self.other, None
            other()
        return self.store.put_if_absent(n, event)


def _two(tmp_path, a_reads_b):
    """Two counters a and b; optionally the ontology of a declares the lineage of b among its inputs."""
    def spec(context):
        return {"criterion.v1.json": {"inputs": {"context": ["mine"], "candidate": {"name": "w", "type": "integer"}},
                                      "body": {"result": "w == mine and w < 3"}},
                "ontology.v1.json": {"inputs": {"context": context}, "returns": "integer", "body": {"result": "mine"}}}
    files = {f"a/{f}": s for f, s in spec(["mine", "other"] if a_reads_b else ["mine"]).items()}
    files.update({f"b/{f}": s for f, s in spec(["mine"]).items()})
    return make_system(tmp_path, {"system": "two", "abstractions": ["a", "b"],
                                  "bindings": {"mine": {"from": "$self", "select": "count"},
                                               "other": {"from": "b", "select": "count"}}}, files)


def _overtake(system, mine, theirs):
    """Z₀ of `mine` judges on Cⁿ; before it appends, `theirs` takes position n. Returns (result, n, realizations)."""
    store = MemoryStore()
    system.run(store, log=quiet, plan=[{"phase": 1}, {"phase": 2}])
    rival_store = store.again()
    rival = Z0(rival_store, {theirs: AbstractionService(rival_store, theirs)})
    racing = Overtaken(store.again(), None)
    service = Counting(racing, mine)
    z0 = Z0(racing, {mine: service})
    n = len(read(racing))
    racing.other = lambda: rival.execute(theirs)
    result, _ = z0.execute(mine)
    assert verify(list(read(store.again()))) == []
    return result, z0.position - n, service.realized


def test_a_lost_race_outside_the_horizon_keeps_the_judgment(tmp_path):
    result, moved, realized = _overtake(_two(tmp_path, a_reads_b=False), "a", "b")
    assert (result, moved, realized) == (ADMITTED, 1, 1)           # appended one position later, computed once


def test_a_lost_race_inside_the_horizon_is_judged_again(tmp_path):
    result, moved, realized = _overtake(_two(tmp_path, a_reads_b=True), "a", "b")
    assert (result, moved, realized) == (ADMITTED, 1, 2)           # b is in the horizon of a: computed again


# ---- the coordinator ----

def test_workers_do_not_continue_a_record(system):
    store = MemoryStore()
    system.run(store, log=quiet)
    with pytest.raises(ValueError, match="empty record"):
        workers.run(System(SQRT2), store, log=quiet)


def test_missing_workers_are_reported(system):
    with pytest.raises(ServiceUnavailable, match="did not all report"):
        workers.run(system, MemoryStore(), local=False, timeout=0.2, log=quiet)


def test_a_failing_worker_stops_the_run(tmp_path):
    system = make_system(tmp_path, {"system": "bad", "abstractions": ["a"]}, {
        "a/criterion.v1.json": {"inputs": {"context": {}, "candidate": {"name": "w", "type": "integer"}},
                                "body": {"result": "True"}},
        "a/ontology.v1.json": {"inputs": {"context": {}}, "returns": "integer", "body": {"result": "1 // 0"}}})
    with pytest.raises(ServiceUnavailable, match="worker a failed: SpecError"):
        workers.run(system, MemoryStore(), log=quiet)


def test_workers_as_separate_processes(tmp_path):
    """Each worker its own process with its own Z₀; the coordinator only runs the plan (execution.local: false)."""
    import subprocess, sys
    from ztes.__main__ import main
    rec, cfg = tmp_path / "rec", tmp_path / "ztes.yaml"
    cfg.write_text(f"store:\n  backend: disk\n  path: {rec}\nexecution:\n  mode: workers\n  local: false\n")
    procs = [subprocess.Popen([sys.executable, "-m", "ztes", "work", str(ROOT / "examples" / "factorization"), a,
                               "--config", str(cfg)], cwd=ROOT)
             for a in ("targets", "primes", "factor")]
    try:
        assert main(["run", str(ROOT / "examples" / "factorization"), "--config", str(cfg)]) == 0
        assert all(p.wait(timeout=10) == 0 for p in procs)         # the coordinator told them to stop
    finally:
        for p in procs:
            p.kill()
    assert verify(list(read(DiskStore(rec)))) == [] and len(read(DiskStore(rec))) == 27


# ---- a worker that fails is a worker that is late ----

class Killed(BaseException):
    """The worker stops at once, as a killed process does: no report, no cleanup."""


class DiesAfterAppending:
    """A handle on the record whose owner may die right after one of its events has been appended."""

    def __init__(self, store, rnd, chance):
        self.store, self.rnd, self.chance = store, rnd, chance
        if hasattr(store, "get_many"):
            self.get_many, self.batch = store.get_many, store.batch
        self.get, self.get_note, self.put_note = store.get, store.get_note, store.put_note

    def put_if_absent(self, n, event):
        done = self.store.put_if_absent(n, event)
        if done and n > 0 and self.rnd.random() < self.chance:
            raise Killed()                                         # the event is in C; the worker never learns it
        return done


def run_with_failures(system, store, seed, chance=0.15):
    """Every worker may be killed before an invocation or right after an append; it is started again."""
    import threading
    rnd, deaths = random.Random(seed), []

    def before_invocation():
        time.sleep(rnd.random() * 0.002)
        if rnd.random() < chance:
            raise Killed()

    def supervise(a):
        while True:
            worker = workers.Worker(system, a, DiesAfterAppending(store.again(), rnd, chance), hesitate=before_invocation)
            try:
                return worker.run()
            except Killed:
                deaths.append(a)
                time.sleep(rnd.random() * 0.005)                   # it stays down for a while

    threads = [threading.Thread(target=supervise, args=(a,), daemon=True) for a in system.abstractions]
    for t in threads:
        t.start()
    workers.run(system, store, local=False, log=quiet)
    for t in threads:
        t.join(timeout=5)
    return deaths


@pytest.mark.parametrize("name", EXAMPLES)
def test_killed_workers_are_restarted_and_nothing_but_time_is_lost(name):
    central, killed = by_agenda(name), 0
    for seed in range(4):
        system, store = System(ROOT / "examples" / name), MemoryStore()
        killed += len(run_with_failures(system, store, seed))
        C = read(store)
        assert verify(list(C)) == []
        assert check_expect(system, C, log=quiet, any_schedule=True) == []
        assert system.states(C) == central[0].states(central[1])
    assert killed, "no worker was killed in any of the runs"


def test_a_restarted_worker_continues_its_source_where_the_record_ends():
    """aco-draw: the draws are a boundary lineage; after any number of failures they are the same draws."""
    _, central = by_agenda("aco-draw")
    system, store = System(ROOT / "examples" / "aco-draw"), MemoryStore()
    assert "draw" in run_with_failures(system, store, seed=1, chance=0.1)
    got, expected = histories(read(store)), histories(central)
    assert got["draw"] == expected["draw"] and got["tour"] == expected["tour"]


def test_a_worker_that_is_down_only_delays_the_run(system):
    """The coordinator waits for a worker that is not there yet; once it runs, the record is the usual one."""
    import threading
    store = MemoryStore()
    late = workers.Worker(system, "upper", store.again())
    threading.Thread(target=workers.Worker(system, "lower", store.again()).run, daemon=True).start()
    threading.Timer(0.3, late.run).start()
    started = time.monotonic()
    workers.run(system, store, local=False, log=quiet)
    assert time.monotonic() - started >= 0.3
    assert histories(read(store))["upper"] == ["3/2", "23/16", "91/64"] and verify(list(read(store))) == []
