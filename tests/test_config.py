"""Configuration (ztes.yaml): it decides where the record is kept and read, never what is recorded."""
import time

import fakeredis
import pytest

from conftest import ROOT, SQRT2, quiet
from ztes import config
from ztes.service import AbstractionService, HttpService, ServiceUnavailable, make_app
from ztes.substrate.replay import verify
from ztes.substrate.store import DiskStore, MemoryStore, NotDurable, RedisStore, read
from ztes.system.system import System

EXAMPLES = sorted(p.name for p in (ROOT / "examples").iterdir() if (p / "system.json").exists())


def record(system, store, services=None):
    system.run(store, services, log=quiet)
    return list(read(store))


@pytest.mark.parametrize("name", EXAMPLES)
def test_the_same_record_under_every_configuration(name, tmp_path):
    """Memory, disk, Redis read one event or seven at a time, services on a replica, services over HTTP."""
    from fastapi.testclient import TestClient
    system = System(ROOT / "examples" / name)
    expected = record(system, MemoryStore())
    assert verify(expected) == []
    assert record(system, DiskStore(tmp_path)) == expected

    server = fakeredis.FakeServer()
    one = RedisStore(client=fakeredis.FakeRedis(server=server), record="one", batch=1)
    assert record(system, one) == expected

    primary = RedisStore(client=fakeredis.FakeRedis(server=server), record="seven", batch=7)
    replica = RedisStore(client=fakeredis.FakeRedis(server=server), record="seven", batch=7)
    assert record(system, primary, system.services(replica, wait=1.0)) == expected

    over_http = RedisStore(client=fakeredis.FakeRedis(server=server), record="http")
    reader = RedisStore(client=fakeredis.FakeRedis(server=server), record="http")
    services = {a: HttpService(client=TestClient(make_app(reader, a, wait=1.0))) for a in system.all_abstractions()}
    assert record(system, over_http, services) == expected


def test_several_records_share_one_database():
    server = fakeredis.FakeServer()
    a = RedisStore(client=fakeredis.FakeRedis(server=server), record="a")
    b = RedisStore(client=fakeredis.FakeRedis(server=server), record="b")
    System(SQRT2).run(a, log=quiet)
    assert len(read(b)) == 0 and len(read(a)) > 1
    assert fakeredis.FakeRedis(server=server).exists("{a}|0", "{b}|0") == 1


class Counted:
    """A store that counts the requests made to it."""

    def __init__(self, store):
        self.store, self.calls = store, 0
        if hasattr(store, "get_many"):
            self.get_many, self.batch = self._get_many, store.batch

    def get(self, n):
        self.calls += 1
        return self.store.get(n)

    def _get_many(self, start, count):
        self.calls += 1
        return self.store.get_many(start, count)

    def put_if_absent(self, n, event):
        self.calls += 1
        return self.store.put_if_absent(n, event)


def test_one_writer_does_not_read_back_what_it_wrote():
    """An admitted event costs one request (the append). An invocation that appends nothing costs
    one too: the check that Cⁿ was still the latest prefix."""
    system = System(ROOT / "examples" / "tsp")
    store = Counted(RedisStore(client=fakeredis.FakeRedis()))
    z0 = system.run(store, log=quiet)
    events = len(read(store))
    silent = sum(o["U"] + o["F"] for o in system.outcomes.values())
    assert store.calls <= events + silent + 8, (store.calls, events, silent)


class Lagging:
    """A replica: it shows an event only `delay` seconds after the primary has it."""

    def __init__(self, primary, delay):
        self.primary, self.delay, self.seen = primary, delay, {}

    def get(self, n):
        e = self.primary.get(n)
        if e is None or time.monotonic() - self.seen.setdefault(n, time.monotonic()) < self.delay:
            return None
        return e


def test_a_service_waits_for_its_replica(system):
    """Replica lag costs time, not correctness: the record is the one obtained without a replica."""
    expected = record(system, MemoryStore())
    primary = MemoryStore()
    assert record(system, primary, system.services(Lagging(primary, 0.01), wait=2.0)) == expected


def test_a_replica_that_stays_behind_stops_the_run(system):
    primary = MemoryStore()
    with pytest.raises(ServiceUnavailable, match="holds 0 events, not C\\^5"):
        system.run(primary, system.services(Lagging(primary, 60), wait=0.05), log=quiet)
    assert verify(list(read(primary))) == []                                  # what was appended is a valid record


class Server(fakeredis.FakeRedis):
    """A Redis whose configuration and replicas the test controls."""
    settings, allow_set, confirming = {}, True, 0

    def config_get(self, name):
        return {name: self.settings.get(name, "no")}

    def config_set(self, name, value):
        if not self.allow_set:
            raise PermissionError("CONFIG is disabled")
        self.settings[name] = value

    def wait(self, replicas, timeout):
        return self.confirming


def test_durability_is_set_or_the_store_does_not_open():
    client = Server()
    client.settings = {}
    RedisStore(client=client, durability="always")
    assert client.settings == {"appendonly": "yes", "appendfsync": "always"}
    managed = Server()
    managed.settings, managed.allow_set = {}, False
    with pytest.raises(NotDurable, match="appendonly = yes"):
        RedisStore(client=managed, durability="everysec")
    managed.settings = {"appendonly": "yes", "appendfsync": "everysec"}
    RedisStore(client=managed, durability="everysec")             # already as required: nothing to set


def test_an_append_no_replica_confirmed_stops_the_run_and_the_run_continues(system):
    expected = record(system, MemoryStore())
    client = Server()
    with pytest.raises(NotDurable, match="0 of 1 replicas"):
        system.run(RedisStore(client=client, replicas=1), log=quiet)
    client.confirming = 1                                         # the replica is back
    assert record(system, RedisStore(client=client, replicas=1)) == expected


def test_the_shipped_file_states_the_defaults():
    assert config.load(ROOT / "ztes.yaml") == config.DEFAULTS


def test_configuration_is_read_checked_and_overridden(tmp_path, monkeypatch):
    f = tmp_path / "ztes.yaml"
    f.write_text("store:\n  backend: redis\n  url: ${ZTES_REDIS}\n  durability: always\nservices:\n  timeout: 3\n")
    monkeypatch.setenv("ZTES_REDIS", "redis://primary:6379/0")
    cfg = config.load(f, {"services.mode": "http", "store.record": None})
    assert cfg["store"]["url"] == "redis://primary:6379/0" and cfg["store"]["durability"] == "always"
    assert cfg["services"] == {**config.DEFAULTS["services"], "timeout": 3, "mode": "http"}
    assert cfg["read"] == config.DEFAULTS["read"] and cfg["store"]["record"] == "C"
    for text, message in (("store:\n  backend: postgres\n", "not one of"),
                          ("store:\n  cache: 5\n", "unknown option store.cache"),
                          ("limits:\n  x: 1\n", "unknown option limits.x"),
                          ("services:\n  timeout: soon\n", "must be a number")):
        f.write_text(text)
        with pytest.raises(config.ConfigError, match=message):
            config.load(f)


def test_run_under_a_configuration_file(tmp_path, capsys):
    from ztes.__main__ import main
    f = tmp_path / "ztes.yaml"
    f.write_text(f"store:\n  backend: disk\n  path: {tmp_path / 'rec'}\n")
    assert main(["run", str(SQRT2), "--config", str(f)]) == 0
    assert f"record: {tmp_path / 'rec'}" in capsys.readouterr().out
    assert main(["verify", "--config", str(f)]) == 0
    f.write_text("store:\n  backend: memory\n")
    assert main(["run", str(SQRT2), "--config", str(f)]) == 0
    assert "in memory" in capsys.readouterr().out
