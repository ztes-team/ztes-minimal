"""Command line: one entry point for every system.

    python -m ztes new     examples/<name> --abstractions a,b   the skeleton of a new system
    python -m ztes check   examples/sqrt2                 check a system without executing it
    python -m ztes design  examples/sqrt2 [--full]        step 0: the abstractions; --full: expanded specifications
    python -m ztes run     examples/sqrt2 [--trace] [--metrics [FILE]] [--http | --services FILE] [--redis URL] [--record DIR]
    python -m ztes serve   examples/sqrt2 lower --port P (--record DIR | --redis URL)
                                                         one abstraction as a separate microservice
    python -m ztes run     examples/sqrt2 --workers       phase 3 by one worker per abstraction (workers.py)
    python -m ztes work    examples/sqrt2 lower (--record DIR | --redis URL)
                                                         one worker as a separate process
    python -m ztes verify  DIR | --redis URL [--judgments]
                                                         R2 replay of an existing record; --judgments:
                                                         re-judge the recorded candidates only (replay.py)
    python -m ztes defects                                the eight defective mechanisms of Table 5

    python -m ztes explain DIR N | --redis URL N          why event N is in the record

run --record DIR on a directory that already holds a record continues that record (system/resume.py).

Where the record is kept and how services are reached is configured in ztes.yaml (config.py):
./ztes.yaml if present, or --config FILE. The options --record, --redis, --http and --services
override the file.
"""
import argparse
import sys
import tempfile

from . import config
from .model import SpecError
from .service import ServiceUnavailable
from .substrate.store import CorruptRecord, NotDurable, read
from .system.resume import DifferentRecord
from .system.report import check_expect, explain_event, report_kpi, report_verification, show, summary
from .system.system import System


def configuration(args):
    """ztes.yaml (or --config FILE), overridden by the options given on the command line."""
    over = {}
    if getattr(args, "redis", None):
        over.update({"store.backend": "redis", "store.url": args.redis})
    elif getattr(args, "record", None):
        over.update({"store.backend": "disk", "store.path": args.record})
    if getattr(args, "http", False):
        over["services.mode"] = "http"
    if getattr(args, "workers", False):
        over["execution.mode"] = "workers"
    if getattr(args, "services", None):
        import json
        with open(args.services, encoding="utf8") as f:
            over["services.urls"] = json.load(f)
    return config.load(getattr(args, "config", None), over)


def main(argv=None):
    """The command line (python -m ztes): parse the arguments and run one command. Returns the exit
    status: 0 when the command succeeded, 1 when a check, a replay or the expected end failed, 2 when
    the command could not be carried out.
    """
    ap = argparse.ArgumentParser(prog="python -m ztes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    nw = sub.add_parser("new", help="create the skeleton of a new system")
    nw.add_argument("path")
    nw.add_argument("--abstractions", required=True, help="comma-separated names")
    nw.add_argument("--title")
    c = sub.add_parser("check", help="check a system without executing it")
    c.add_argument("system")
    d = sub.add_parser("design", help="show the abstractions of a system (step 0)")
    d.add_argument("system")
    d.add_argument("--full", action="store_true", help="print every specification in its expanded, recorded form")
    r = sub.add_parser("run", help="execute the plan of a system and verify the record")
    r.add_argument("system")
    r.add_argument("--http", action="store_true", help="run each abstraction as an HTTP microservice")
    r.add_argument("--trace", action="store_true", help="show bindings and intermediate values of every invocation")
    r.add_argument("--services", help="JSON file: abstraction → URL of a running `serve` process")
    r.add_argument("--metrics", nargs="?", const="-", metavar="FILE",
                   help="KPI at the end of the plan (if it has no KPI step) and their table; FILE: also as JSON")
    r.add_argument("--workers", action="store_true", help="phase 3 by one worker per abstraction, each with its own Z₀")
    w = sub.add_parser("work", help="run one abstraction as a worker with its own Z₀, on the shared record")
    w.add_argument("system")
    w.add_argument("abstraction")
    w.add_argument("--record", help="directory of the shared local record")
    w.add_argument("--redis", help="Redis URL of the shared record")
    sv = sub.add_parser("serve", help="run one abstraction as an HTTP microservice")
    sv.add_argument("system")
    sv.add_argument("abstraction")
    sv.add_argument("--port", type=int, required=True)
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--record", help="directory of the shared local record")
    sv.add_argument("--redis", help="Redis URL of the shared record")
    r.add_argument("--redis", help="Redis URL for a distributed record")
    r.add_argument("--record", help="directory for a local record (default: a new temporary one)")
    v = sub.add_parser("verify", help="replay an existing record (R2)")
    v.add_argument("record", nargs="?")
    v.add_argument("--redis")
    v.add_argument("--judgments", action="store_true",
                   help="judge the recorded candidates without re-deriving them: faster, but a candidate "
                        "that does not follow from the record is not found (see replay.py)")
    sub.add_parser("defects", help="the eight defective mechanisms of Table 5, and what replay finds")
    x = sub.add_parser("explain", help="explain why an event is in an existing record")
    x.add_argument("args", nargs="+", help="DIR N, or N with --redis")
    x.add_argument("--redis")
    for command in (r, sv, w, v, x):
        command.add_argument("--config", metavar="FILE", help="configuration (default: ./ztes.yaml if present)")
    args = ap.parse_args(argv)

    if args.cmd == "defects":
        from .defects import report
        return 0 if all(first for _, _, first in report()) else 1
    if args.cmd == "new":
        from .system.scaffold import new_system
        root = new_system(args.path, [a.strip() for a in args.abstractions.split(",") if a.strip()], args.title)
        print(f"created {root}; next: edit DESIGN.md and the specifications, then python -m ztes check {root}")
        return 0
    try:
        cfg = configuration(args) if args.cmd in ("run", "serve", "work", "verify", "explain") else None
    except config.ConfigError as x:
        ap.error(str(x))
    if args.cmd == "explain":
        if not args.redis and len(args.args) > 1:
            cfg["store"].update(backend="disk", path=args.args[0])
        explain_event(read(config.open_store(cfg)), int(args.args[-1]))
        return 0
    if args.cmd == "serve":
        import uvicorn
        from .service import make_app
        system = System(args.system)
        if args.abstraction not in system.abstractions:
            ap.error(f"{args.abstraction} is not an abstraction of {system.name}")
        if cfg["store"]["backend"] == "memory" or (cfg["store"]["backend"] == "disk" and not cfg["store"]["path"]):
            ap.error("serve needs the shared record: --record DIR, --redis URL, or a store in ztes.yaml")
        cfg["store"].update(durability=None, replicas=0)       # a service only reads
        store = config.open_reader(cfg, config.open_store(cfg))
        uvicorn.run(make_app(store, args.abstraction, cfg["read"]["wait"]),
                    host=args.host, port=args.port, log_level="warning")
        return 0
    if args.cmd == "work":
        from .system.workers import Worker
        system = System(args.system)
        if cfg["store"]["backend"] == "memory" or (cfg["store"]["backend"] == "disk" and not cfg["store"]["path"]):
            ap.error("work needs the shared record: --record DIR, --redis URL, or a store in ztes.yaml")
        if args.abstraction not in system.abstractions:      # it may be brought in during the run (governance.py)
            print(f"{args.abstraction} is not declared in {system.name}: its worker waits until a candidate "
                  "carries its specifications")
        Worker(system, args.abstraction, config.open_store(cfg), cfg["execution"]["poll"]).run()
        return 0
    if args.cmd == "check":
        return 1 if System(args.system).check() else 0
    if args.cmd == "design":
        system = System(args.system)
        system.describe()
        if args.full:
            import json
            for key, s in system.specs.items():
                print(f"\n{key}\n" + json.dumps(s, indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "run":
        system = System(args.system)
        if system.check(log=lambda *_: None):          # a malformed system is not executed
            system.check()
            return 1
        by_workers = cfg["execution"]["mode"] == "workers"
        try:
            store = config.open_store(cfg)
            services = None if by_workers else config.open_services(cfg, system, store)
        except (config.ConfigError, NotDurable) as x:
            print(f"not started:\n   {type(x).__name__}: {x}")
            return 2
        system.describe()
        try:
            plan = system.plan
            if args.metrics and not any(step.get("kpi") for step in plan):
                plan = plan + [{"kpi": True}]                  # the indicators, once, at the end
            if by_workers:
                from .system import workers
                x = cfg["execution"]
                workers.run(system, store, x["local"], x["poll"], x["timeout"], plan=plan)
            else:
                system.run(store, services, trace=args.trace, plan=plan)
        except SpecError as x:                             # a specification failed: say where, stop
            show(read(store))
            print(f"\nerror in a specification, execution stopped:\n   {x}")
            return 2
        except (CorruptRecord, DifferentRecord, ServiceUnavailable) as x:   # nothing was appended
            print(f"\nexecution stopped, the record is unchanged:\n   {type(x).__name__}: {x}")
            return 2
        except NotDurable as x:                            # appended on the primary, not yet confirmed
            print(f"\nexecution stopped:\n   {x}\n   run the same command again to continue from the record")
            return 2
        C = read(store)
        show(C)
        summary(system, C)
        if args.metrics:
            kpi = report_kpi(system, C)
            if args.metrics != "-" and kpi is not None:
                import json
                with open(args.metrics, "w", encoding="utf8") as f:
                    json.dump({"system": system.name, **kpi}, f, indent=2, ensure_ascii=False)
                print(f"   written to {args.metrics}")
        print(f"\nrecord: {config.where(cfg, store)}")
        failed = report_verification(C)
        return 1 if (check_expect(system, C, any_schedule=by_workers) or failed) else 0
    if args.cmd == "verify":
        if cfg["store"]["backend"] == "memory" or (cfg["store"]["backend"] == "disk" and not cfg["store"]["path"]):
            ap.error("verify needs a record: a directory, --redis URL, or a store in ztes.yaml")
        C = read(config.open_store(cfg), check=False)             # the verifier says where a record fails
        show(C)
        return 1 if report_verification(C, judgments_only=args.judgments) else 0


if __name__ == "__main__":
    sys.exit(main())
