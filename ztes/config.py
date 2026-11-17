"""How a system is run: one file, ztes.yaml.

system.json says what is executed: abstractions, specifications, plan, sources and their seeds.
ztes.yaml says on what: where the record is kept, how durable it is, where services read it
and how Z₀ reaches them. Nothing in ztes.yaml can change the record: the same system gives the
same events under every configuration (tests/test_config.py). What can change the record,
such as "admission_limit" or the seed of a source, is therefore not here.

The file is looked for as ./ztes.yaml, or named with --config FILE; without a file the
defaults below hold. A value "${NAME}" is taken from the environment, so one file serves
every container. Command-line options (--record, --redis, --http, --services, --workers) override
the file.

One option does change the order of events: execution.mode. With workers, which abstraction
appends first is decided by their race, as Axiom 0 allows. Every record so obtained is valid
(R2). An abstraction whose result is determined by its inputs has the same history as under the
agenda; one that resolves against the context it finds (D1) may take another, equally valid course.
"""
import copy
import os
import tempfile

FILE = "ztes.yaml"

DEFAULTS = {
    "store": {
        "backend": "disk",                    # memory | disk | redis
        "path": None,                         # disk: the directory of the record (None: a new temporary one)
        "url": "redis://localhost:6379/0",    # redis: the primary, the only place Z₀ appends
        "record": "C",                        # redis: the name of the record; several may share one database
        "durability": None,                   # redis: always | everysec | none (None: the server as it is)
        "replicas": 0,                        # redis: replicas that must confirm every append
        "replica_timeout_ms": 1000,           # redis: how long Z₀ waits for that confirmation
        "batch": 256,                         # redis: events fetched by one read
    },
    "execution": {
        "mode": "central",                    # central: one agenda and one Z₀ | workers: one Z₀ per abstraction
        "local": True,                        # workers: started here as threads (false: they run elsewhere, `ztes work`)
        "poll": 0.002,                        # workers: seconds between two looks at the record while waiting
        "timeout": 60.0,                      # workers: seconds the coordinator waits for them before it gives up
    },
    "read": {
        "url": None,                          # redis: a replica the services read (None: the primary)
        "wait": 5.0,                          # seconds a service waits until its store holds Cⁿ
    },
    "services": {
        "mode": "inprocess",                  # inprocess | http (one local HTTP service per abstraction)
        "urls": {},                           # abstraction → URL of a running `python -m ztes serve`
        "timeout": 10.0,                      # seconds Z₀ waits for one answer of a service
        "retries": 2,                         # further attempts after a call that failed in transport
        "base_port": 8701,                    # http: the port of the first local service
        "startup": 1.0,                       # http: seconds given to local services to start
    },
}

CHOICES = {("store", "backend"): ("memory", "disk", "redis"),
           ("store", "durability"): (None, "always", "everysec", "none"),
           ("services", "mode"): ("inprocess", "http"),
           ("execution", "mode"): ("central", "workers")}


class ConfigError(ValueError):
    """ztes.yaml names a section, key or value that does not exist."""


def load(path=None, overrides=None):
    """The configuration: the defaults, then the file, then `overrides` ({"store.backend": "redis", …})."""
    cfg = copy.deepcopy(DEFAULTS)
    if path is None and os.path.exists(FILE):
        path = FILE
    if path is not None:
        import yaml
        with open(path, encoding="utf8") as f:
            given = yaml.safe_load(f) or {}
        if not isinstance(given, dict):
            raise ConfigError(f"{path}: expected sections {sorted(DEFAULTS)}")
        for section, values in given.items():
            for key, value in (values or {}).items() if isinstance(values, dict) else [(None, None)]:
                _set(cfg, section, key, value, path)
    for dotted, value in (overrides or {}).items():
        if value is not None:
            _set(cfg, *dotted.split("."), value, "command line")
    return cfg


def _set(cfg, section, key, value, origin):
    """Set one option of the configuration: it must exist, have an allowed value and the type of its
    default (a boolean, or a number not below zero); environment variables in a text are expanded.
    origin names where the value came from, for the error message.
    """
    if section not in cfg or key not in cfg[section]:
        raise ConfigError(f"{origin}: unknown option {section}.{key}; "
                          f"known: {', '.join(f'{s}.{k}' for s in DEFAULTS for k in DEFAULTS[s])}")
    if isinstance(value, str):
        value = os.path.expandvars(value)
    allowed = CHOICES.get((section, key))
    if allowed and value not in allowed:
        raise ConfigError(f"{origin}: {section}.{key} = {value!r} is not one of {list(allowed)}")
    default = DEFAULTS[section][key]
    if isinstance(default, bool):
        if not isinstance(value, bool):
            raise ConfigError(f"{origin}: {section}.{key} = {value!r} must be true or false")
        default = None
    if isinstance(default, (int, float)) and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
        raise ConfigError(f"{origin}: {section}.{key} = {value!r} must be a number ≥ 0")
    if isinstance(default, dict) and not isinstance(value, dict):
        raise ConfigError(f"{origin}: {section}.{key} must map abstraction names to URLs")
    cfg[section][key] = value


def open_store(cfg):
    """The store of the record, where Z₀ appends."""
    from .substrate.store import DiskStore, MemoryStore, RedisStore
    s = cfg["store"]
    if s["backend"] == "memory":
        return MemoryStore()
    if s["backend"] == "disk":
        return DiskStore(s["path"] or tempfile.mkdtemp(prefix="C_"))
    return RedisStore(s["url"], record=s["record"], durability=s["durability"], replicas=s["replicas"],
                      replica_timeout_ms=s["replica_timeout_ms"], batch=s["batch"])


def open_reader(cfg, store):
    """The store the abstraction services read: a replica if read.url names one, otherwise `store`.

    Services only read, and what they read is a prefix Cⁿ that never changes, so a replica
    serves as well as the primary. A replica that does not yet hold Cⁿ makes the service wait
    (read.wait); it never makes it answer on a shorter prefix.
    """
    from .substrate.store import RedisStore
    if cfg["store"]["backend"] == "redis" and cfg["read"]["url"]:
        return RedisStore(cfg["read"]["url"], record=cfg["store"]["record"], batch=cfg["store"]["batch"])
    return store


def open_services(cfg, system, store):
    """One service per abstraction, as "services" says: in process, local HTTP, or already running."""
    from .service import HttpService
    s, wait = cfg["services"], cfg["read"]["wait"]

    def client(url):
        """A client for the abstraction service at url, with the timeout and the retries of the configuration."""
        return HttpService(url, timeout=s["timeout"], retries=s["retries"])

    if s["urls"]:
        missing = [a for a in system.abstractions if a not in s["urls"]]
        if missing:
            raise ConfigError(f"services.urls has no URL for {missing}")
        return {a: client(s["urls"][a]) for a in system.abstractions}
    return system.services(open_reader(cfg, store), http=s["mode"] == "http", base_port=s["base_port"],
                           wait=wait, client=client, startup=s["startup"])


def where(cfg, store):
    """Where the record is, in words, for the end of a run."""
    s = cfg["store"]
    if s["backend"] == "redis":
        return f"{s['url']} (record {s['record']})"
    return store.c.directory if s["backend"] == "disk" else "in memory, gone with this process"
