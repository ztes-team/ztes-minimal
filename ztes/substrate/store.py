"""[Z₀][C] The physical medium of C: a key-value store with one atomic write.   Paper: S1.1, §4.2.5, §9.1

C is append-only: a stored event is never changed. The single write operation is put_if_absent: an atomic
conditional insert of one event at position n (§9.1: "the append of one
event is the only primitive state change that must be atomic").

The key of an event is its position n in C. This is what ties a judgment
to its prefix: Z₀ judges a candidate on C^n and may store the
event only at position n. If another instance of Z₀ has written n in the
meantime, the insert fails and the invocation is judged again on the
extended prefix (Axiom 0 with S1.5, recording before activation).

Any key-value store with an atomic conditional insert realizes this
interface (§4.7, §9.5); three backends are given: in memory (for checks and
tests), diskcache (local, the default), and Redis (distributed).

Beside the record a store keeps notes: small values under a name, overwritten freely. They are
not events and no judgment reads them; workers and their coordinator use them to tell each other
how far they are (system/workers.py). again() opens the same record once more, for another
thread or instance of Z₀: each keeps what it has read for itself.
"""
import json

from ..model.view import Index, Record
from . import events


class CorruptRecord(Exception):
    """The stored record is not a chain of events: a position or a hash link is wrong (S1.1, S1.5)."""


class MemoryStore:
    """In-memory backend: for static checks and tests; the record disappears with the process."""

    def __init__(self):
        import threading
        self.c, self.notes, self.lock = {}, {}, threading.Lock()

    def get(self, n):
        return self.c.get(n)

    def put_if_absent(self, n, event):
        with self.lock:                                        # atomic among the threads of this process
            if n in self.c:
                return False
            self.c[n] = event
            return True

    def get_note(self, name):
        return self.notes.get(name)

    def put_note(self, name, value):
        self.notes[name] = value

    def again(self):
        other = MemoryStore()
        other.c, other.notes, other.lock = self.c, self.notes, self.lock
        return other


def key(n, record=None):
    """The key of position n: "C|n" in a store that holds one record (a directory), "{record}|n"
    in a store shared by several. The braces are a Redis hash tag: in a cluster they keep all
    events of one record on one node, which the single order of C requires (S1.1).
    """
    return f"C|{n}" if record is None else f"{{{record}}}|{n}"


class DiskStore:
    """Local backend (diskcache). Atomic across processes on one machine; the record is one directory."""

    def __init__(self, path):
        import diskcache
        self.c = diskcache.Cache(path)

    def get(self, n):
        """Read the event at position n, or None if C is shorter."""
        return self.c.get(key(n))

    def put_if_absent(self, n, event):
        """Atomic conditional insert: succeeds only if position n is still free."""
        return self.c.add(key(n), event)

    def get_note(self, name):
        return self.c.get(f"note|{name}")

    def put_note(self, name, value):
        self.c.set(f"note|{name}", value)

    def again(self):
        return DiskStore(self.c.directory)


class NotDurable(Exception):
    """The store does not give the durability the configuration asks for; nothing was started or appended further."""


# what "durability" means for Redis: the settings the server must have
REDIS_DURABILITY = {"always": {"appendonly": "yes", "appendfsync": "always"},
                    "everysec": {"appendonly": "yes", "appendfsync": "everysec"},
                    "none": {}}


class RedisStore:
    """Distributed backend (Redis). SET ... NX is atomic for all clients of one primary.

        record      the name of the record: several records may share one database
        durability  "always": every append is on disk before it is acknowledged; "everysec": at
                    most one second of acknowledged events can be lost if the server fails;
                    "none": memory only. The server is checked when the store is opened; where
                    the server allows it the setting is made, otherwise the store refuses to
                    open (NotDurable). None: the server is used as it is.
        replicas    how many replicas must confirm an append (WAIT) before it counts. An event
                    not confirmed in time stops the run: it is on the primary, and the same plan
                    continues from the record once the replicas have it.
        batch       how many events one read asks for (MGET)
    """

    def __init__(self, url="redis://localhost:6379/0", client=None, record="C", durability=None,
                 replicas=0, replica_timeout_ms=1000, batch=256):
        if client is None:
            import redis
            client = redis.Redis.from_url(url)
        self.r, self.record, self.batch = client, record, batch
        self.replicas, self.replica_timeout_ms = replicas, replica_timeout_ms
        if durability is not None:
            self._require(durability)

    def _require(self, durability):
        if durability not in REDIS_DURABILITY:
            raise ValueError(f"durability {durability!r} is not one of {sorted(REDIS_DURABILITY)}")
        for name, wanted in REDIS_DURABILITY[durability].items():
            try:
                have = self.r.config_get(name).get(name)
                have = have.decode() if isinstance(have, bytes) else have
                if have != wanted:
                    self.r.config_set(name, wanted)
            except Exception as x:                              # managed servers do not allow CONFIG
                raise NotDurable(f"durability {durability!r} needs {name} = {wanted}; the server "
                                 f"neither confirms it nor lets it be set ({type(x).__name__}: {x})") from x

    def get(self, n):
        v = self.r.get(key(n, self.record))
        return None if v is None else json.loads(v)

    def get_many(self, start, count):
        """The events at positions start … start + count − 1 that exist, in order, in one round trip."""
        out = []
        for v in self.r.mget([key(n, self.record) for n in range(start, start + count)]):
            if v is None:
                break
            out.append(json.loads(v))
        return out

    def put_if_absent(self, n, event):
        if not self.r.set(key(n, self.record), json.dumps(event), nx=True):
            return False
        if self.replicas:
            confirmed = self.r.wait(self.replicas, self.replica_timeout_ms)
            if confirmed < self.replicas:
                raise NotDurable(f"event {n} is on the primary but only {confirmed} of {self.replicas} "
                                 f"replicas confirmed it within {self.replica_timeout_ms} ms")
        return True

    def get_note(self, name):
        v = self.r.get(f"{{{self.record}}}|note|{name}")
        return None if v is None else json.loads(v)

    def put_note(self, name, value):
        self.r.set(f"{{{self.record}}}|note|{name}", json.dumps(value))

    def again(self):
        return RedisStore(client=self.r, record=self.record, replicas=self.replicas,
                          replica_timeout_ms=self.replica_timeout_ms, batch=self.batch)


def read(store, n=None, check=True):
    """[C] The recorded prefix Cⁿ as a view (model.view.Record); without n, the whole record so far.

    Every event is checked once, when it is first read: it must stand at its position and carry
    the hash of the event before it. A record that fails is not executed on (CorruptRecord): Z₀
    never judges on a prefix that is not a chain. The verifier reads with check=False, because
    its task is to say where and why a record fails.

    C is append-only (S1.1), so events already read never change: they are kept in a cache on
    the store object, together with their index, and only events not yet read are fetched.
    Each store object therefore reads every event once, also when other processes append to
    the same record. With n, the store is consulted only if fewer than n events are cached:
    a service evaluating on Cⁿ, which Z₀ has just read, costs no access to the store.
    """
    cache = store.__dict__.setdefault("_cache", [])
    ix = store.__dict__.setdefault("_index", Index())
    many = getattr(store, "get_many", None)                           # a store that reads in batches
    while n is None or len(cache) < n:
        if many is None:
            got = [e] if (e := store.get(len(cache))) is not None else []
        else:
            want = store.batch if n is None else min(store.batch, n - len(cache))
            got = many(len(cache), want)
        for e in got:
            _keep(store, e, check)
        if not got or (many is not None and n is None and len(got) < want):
            break                                                      # the end of what is stored
    return Record(cache, len(cache) if n is None else min(n, len(cache)), ix)


def _keep(store, e, check=True):
    """Add the next event to what this store object has read: checked, hashed and indexed once."""
    cache, ix = store.__dict__["_cache"], store.__dict__["_index"]
    last = store.__dict__.setdefault("_last", [events.GENESIS])       # hash of the last event read
    if check and (e["coord"].get("n") != len(cache) or e["coord"].get("prev") != last[0]):
        raise CorruptRecord(f"event {len(cache)} is not linked to the event before it")
    last[0] = events.addr(e)
    ix.add(len(cache), e)
    cache.append(e)


def known(store):
    """The record as far as this store object has read it, without asking the store (None: nothing read yet)."""
    cache = store.__dict__.get("_cache")
    return None if cache is None else Record(cache, len(cache), store.__dict__["_index"])


def wrote(store, n, event):
    """Z₀ has just appended `event` at position n: it is known here without being read back."""
    cache = store.__dict__.get("_cache")
    if cache is not None and len(cache) == n:
        _keep(store, event)


def tip(store, C):
    """The hash of the last event of C if C is the whole record read so far from this store, else None."""
    last = store.__dict__.get("_last")
    return last[0] if last and len(C) == len(store.__dict__.get("_cache", ())) else None
