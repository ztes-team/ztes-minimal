"""Reports on C: the record as text, why an event is in it, the comparison with "expect", R2.
"""
import json
from fractions import Fraction

from ..model import explain as explaining
from ..substrate import lookups
from ..substrate.governance import refusal
from ..model.types import canon
from ..substrate.replay import verify


def show(C, log=print):
    """Print the record, one event per line: an execution event with its value, a specification with
    its role, version and address.
    """
    log(f"\n{'n':>4}  {'kind':7} {'abstraction':12} value")
    for e in C:
        c = e["coord"]
        if c["kind"] == "exec":
            p = e["payload"]
            log(f"{c['n']:>4}  exec    {c['abstraction']:12} {_text(p)}{_decimal(p)}")
        elif c["kind"] == "spec":
            log(f"{c['n']:>4}  spec    {c['abstraction']:12} {c['role']} v{c['version']}   addr {c['addr'][:16]}…")
        else:
            log(f"{c['n']:>4}  {c['kind']}")


def summary(system, C, log=print):
    """The run in a few lines: for every abstraction what was admitted, what was not, and how it ended."""
    from ..system import agenda
    states = agenda.states(system, C)
    words = {"closed": "closed (τ false)", "wait": "waits (Not Yet)", "wait-external": "waits on an external lineage"}
    kinds = [e["coord"]["kind"] for e in C]
    log(f"\nSummary  {len(C)} events: {kinds.count('spec')} specifications, {kinds.count('exec')} admitted results")
    log("   Not Yet (ω = ⊥): horizon = a required event is not in Cⁿ, nothing computed; "
        "body = computed, no candidate.  τ false: a candidate, refused on this prefix")
    log(f"   {'abstraction':14} {'invoked':>8} {'admitted':>9} {'horizon':>8} {'body':>5} {'τ false':>8}   end, and the last admitted value")
    for a in system.abstractions:
        c = system.outcomes.get(a, {})
        last = next((e["payload"] for e in reversed(list(C))
                     if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == a), None)
        value = "" if last is None else _text(last)
        value = value if len(value) <= 60 else value[:58] + " …"
        log(f"   {a:14} {c.get('I', 0):>8} {c.get('A', 0):>9} {c.get('H', 0):>8} {c.get('U', 0) - c.get('H', 0):>5} "
            f"{c.get('F', 0):>8}   {words[states[a]]}"
            + (f"; {value}" if value else ""))


def _text(p):
    """A payload as text: strings as they are, other JSON values in JSON notation."""
    return p if isinstance(p, str) else json.dumps(p, ensure_ascii=False)


def _decimal(p):
    """For rational payloads "p/q", also show the decimal value."""
    if isinstance(p, str) and "/" in p:
        try:
            return f"   ≈ {float(Fraction(p)):.6f}"
        except (ValueError, ZeroDivisionError):
            pass
    return ""


def report_verification(C, log=print, judgments_only=False):
    """Replay the record (R2) and print the outcome, with every event that fails; returns the failures.
    judgments_only: judge the recorded candidates without re-deriving them (replay.py).
    """
    errors = verify(C, judgments_only)
    mode = " (judgments only: the candidates are not re-derived)" if judgments_only else ""
    log(f"\nR2  replay of {len(C)} events{mode}: " + ("OK" if not errors else "FAILED"))
    for n, why in errors:
        log(f"   event {n}: {why}")
    return errors


def explain_event(C, n, log=print):
    """Why the event at position n is in the record: its prefix, its specifications, its judgment."""
    e, P = C[n], C[:n]
    c = e["coord"]
    log(f"event {n}: {c['kind']}" + (f" of {c['abstraction']}" if "abstraction" in c else ""))
    if c["kind"] == "genesis":
        log("  the fixed starting event of Z₀; τ_root is the first registered criterion")
    elif c["kind"] == "spec":
        s = e["payload"]
        why = refusal(P, s)
        log(f"  {c['role']} v{c['version']}, address {c['addr']}, admitted under τ_root: "
            + ("True" if why is None else f"False ({why})"))
        if c["role"] == "ontology":
            log(f"  lineage: bound to the criterion {s['criterion']} active in C^{n}")
        log(f"  horizon: {lookups.lineages(s)}")
    else:
        log(f"  judged on C^{n} with ontology {c['ontology']} and criterion {c['criterion']}")
        for line in explaining.explain(P, lookups.load(P, c["ontology"])):
            log("  " + line)
        for line in explaining.explain(P, lookups.load(P, c["criterion"]), e["payload"]):
            log("  " + line)
        log(f"  recorded payload: {_text(e['payload'])}")


def check_expect(system, C, log=print, any_schedule=False):
    """Compare the end of a run with "expect" in system.json. Returns a list of differences.

    any_schedule: the run was executed by workers, so the order of invocations was not that of
    the agenda. What must hold then is "any_schedule" inside "expect", if the system states it
    (with "last": abstraction → the fields of its last admitted value); otherwise all of
    "expect" holds under every schedule. Indicators count invocations and are not compared.
    """
    e, diffs = system.expect, []
    if not e:
        return diffs
    if any_schedule:
        e = {"states": e.get("states", {}), **e["any_schedule"]} if "any_schedule" in e else dict(e)
        e["values"] = {a: v for a, v in e.get("values", {}).items() if a != system.kpi}
    n = len(C)
    if not any(step.get("kpi") for step in system.plan):       # KPI added by --metrics: not part of expect
        above = {"profile"} | ({system.kpi} if system.kpi else set())
        n -= sum(1 for x in C if x["coord"].get("abstraction") in above)
    if "events" in e and n != e["events"]:
        diffs.append(f"events: {n}, expected {e['events']}")
    if "states" in e:
        got = system.states(C)
        diffs += [f"state of {a}: {got.get(a)}, expected {s}" for a, s in e["states"].items() if got.get(a) != s]
    for a, vs in e.get("values", {}).items():
        got = [x["payload"] for x in C if x["coord"]["kind"] == "exec" and x["coord"]["abstraction"] == a]
        if got != vs:
            diffs.append(f"values of {a}: {got}, expected {vs}")
    for a, fields in e.get("last", {}).items():
        got = [x["payload"] for x in C if x["coord"]["kind"] == "exec" and x["coord"]["abstraction"] == a]
        if not got or any(got[-1].get(k) != v for k, v in fields.items()):
            diffs.append(f"last value of {a}: {got[-1] if got else None}, expected {fields}")
    log("\nExpect  " + ("OK" if not diffs else f"{len(diffs)} difference(s)")
        + ("   (what holds under any schedule)" if any_schedule else ""))
    for d in diffs:
        log(f"   {d}")
    return diffs


def record_size(C):
    """Events of C and their size in canonical JSON, by kind: {kind: (events, bytes)}."""
    out = {}
    for e in C:
        k = e["coord"]["kind"]
        n, b = out.get(k, (0, 0))
        out[k] = (n + 1, b + len(canon(e).encode()))
    return out


def report_kpi(system, C, log=print):
    """The execution indicators recorded in C (the latest profile and KPI events) as a table and as data."""
    from .kpi import table
    rows, measured = table(system, C)
    if not rows:
        log("\nKPI  no profile recorded: add {\"kpi\": true} to the plan, or run with --metrics")
        return None
    states = system.states(C)
    log("\nKPI  (I invocations, A admitted, U ⊥ Not Yet, of which H by the horizon alone, F τ false, α = A/I),"
        " from the latest profile in C")
    log(f"   {'abstraction':14}{'I':>7}{'A':>7}{'U':>7}{'H':>7}{'F':>6}{'α':>7}  state")
    for a in system.abstractions:
        r = rows.get(a, {"I": 0, "A": 0, "U": 0, "H": 0, "F": 0})
        alpha = f"{r['A'] / r['I']:.2f}" if r["I"] else "–"
        log(f"   {a:14}{r['I']:>7}{r['A']:>7}{r['U']:>7}{r['H']:>7}{r['F']:>6}{alpha:>7}  {states.get(a, '')}")
    tot = {k: sum(r[k] for r in rows.values()) for k in ("I", "A", "U", "H", "F")}
    log(f"   {'total':14}{tot['I']:>7}{tot['A']:>7}{tot['U']:>7}{tot['H']:>7}{tot['F']:>6}"
        f"{(f'{tot['A'] / tot['I']:.2f}' if tot['I'] else '–'):>7}")
    if measured is not None:
        log(f"   {system.kpi}: " + json.dumps(measured, ensure_ascii=False))
    sizes = record_size(C)
    log("   record  " + ", ".join(f"{k}: {n} events, {b / 1024:.1f} KB" for k, (n, b) in sizes.items()))
    return {"abstractions": [{"abstraction": a, **rows.get(a, {})} for a in system.abstractions],
            "kpi": measured, "states": states,
            "record": {k: {"events": n, "bytes": b} for k, (n, b) in sizes.items()}}
