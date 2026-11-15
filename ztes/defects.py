"""Eight defective mechanisms, one for each essential condition of S1.   Paper: Theorems C, C′, D; Table 5

Theorem C says that no condition of S1 can be omitted; Theorem D calls what a mechanism does when
it omits one a *deviation*. This module performs each deviation once, on the ant colony of
examples/aco (and examples/aco-draw for the hidden draw), and lets the verifier (replay.py) say
what breaks. Each defect is something an ordinary implementation of the method would do:

    1  append-only            evaporation overwrites a stored tour in place
    2  shared order           a colony that has not seen a governing event keeps admitting
    3  recorded inputs        the random generator is kept outside the record
    4  immutable versions     a parameter is changed inside a recorded specification
    5  endogenous activation  an operator switches the rule without any event
    6  retained evidence      only the length of a tour is stored, not the tour
    7  certification          a tour is appended although its criterion is false
    8  record, then activate  a new criterion judges before its own event is recorded

Nothing here is part of Z₀: every defect builds a record that Z₀ would not have written, and the
check is the ordinary replay, which reads only that record.

    python -m ztes defects            the table: defect, where replay stops, why
"""
import copy
from pathlib import Path

from .model import realize
from .substrate import events, lookups
from .substrate.replay import lost, verify
from .substrate.store import MemoryStore, read
from .system.authoring import read_directory
from .system.system import System

EXAMPLES = Path(__file__).parent.parent / "examples"
quiet = lambda *_: None


def run(name, admissions=None):
    """The record of an example as a list of events; with `admissions`, phase 3 stops after that many."""
    d = read_directory(EXAMPLES / name)
    if admissions is not None:
        d["plan"] = [{"phase": 1}, {"phase": 2}, {"phase": 3, "max_admissions": admissions}]
        d.pop("expect", None)
    system, store = System.from_dict(d), MemoryStore()
    system.run(store, log=quiet)
    return system, copy.deepcopy(list(read(store)))


def relink(C):
    """Positions and hash links recomputed: what a mechanism without a stable history would hold."""
    out = []
    for e in C:
        out.append({"coord": {**e["coord"], "n": len(out), "prev": events.link(out)}, "payload": e["payload"]})
    return out


def position(C, abstraction, k):
    """The position of the k-th execution event of an abstraction."""
    return [n for n, e in enumerate(C) if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == abstraction][k]


def version2(system, key, **constants):
    """A second version of a specification of the system, with some constants changed."""
    s = copy.deepcopy(system.specs[key])
    s["version"], s["constants"] = 2, {**s["constants"], **constants}
    return s


def stale_event(C, P, abstraction):
    """The event a writer would append to C after judging on the older prefix P."""
    o, t = lookups.active(P, abstraction, "ontology"), lookups.active(P, abstraction, "criterion")
    w = realize(P, lookups.load(P, o))
    return events.rec(C, {"kind": "exec", "abstraction": abstraction, "ontology": o, "criterion": t}, w)


# ---- the eight deviations ----------------------------------------------------------------------

def overwrite():
    """1. Evaporation as an update: the stored tour of ant 3 is replaced by that of ant 2."""
    _, C = run("aco", 14)
    n, m = position(C, "tour", 3), position(C, "tour", 2)
    C[n]["payload"] = {**C[m]["payload"], "k": 3}
    return C


def stale_order():
    """2. A governing event closes the lineage (T = 5), but a writer that has not seen it admits another tour."""
    system, P = run("aco", 14)
    C = P + [events.spec_event(P, version2(system, "tour/criterion.v1", T=5))]
    return C + [stale_event(C, P, "tour")]


def hidden_draw():
    """3. The classical colony with its generator outside the record: the draws were never admitted."""
    _, C = run("aco-draw", 24)
    return relink([e for e in C if not (e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == "draw")])


def mutated_version():
    """4. BETA is changed from 2 to 3 inside the recorded ontology of tour, at the same address."""
    _, C = run("aco", 14)
    n = next(n for n, e in enumerate(C) if e["coord"]["kind"] == "spec"
             and (e["coord"]["abstraction"], e["coord"]["role"]) == ("tour", "ontology"))
    C[n]["payload"]["constants"]["BETA"] = 3
    return relink(C)


def exogenous_activation():
    """5. An operator switches the window to K = 4; no event records the new version."""
    system, C = run("aco", 14)
    s = version2(system, "tour/ontology.v1", K=4)
    s["criterion"] = lookups.active(C, "tour", "criterion")
    coord = {"kind": "exec", "abstraction": "tour", "ontology": events.addr(s), "criterion": s["criterion"]}
    return C + [events.rec(C, coord, realize(C, s))]


def lossy_evidence():
    """6. Only what the pheromone needs is stored: the number and the length of a tour, not its walk."""
    _, C = run("aco", 14)
    for e in C:
        if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == "tour":
            e["payload"] = {**e["payload"], "walk": []}
    return relink(C)


def uncertified():
    """7. The budget is spent and the criterion is false, but one more tour is appended."""
    _, C = run("aco")
    C = [e for e in C if e["coord"].get("abstraction") not in ("profile", "kpi")]
    return C + [stale_event(C, C, "tour")]


def activation_first():
    """8. A new criterion is switched on, judges a tour, and only then is its own event recorded."""
    system, C = run("aco", 14)
    s = version2(system, "tour/criterion.v1", T=100)
    o = lookups.active(C, "tour", "ontology")
    coord = {"kind": "exec", "abstraction": "tour", "ontology": o, "criterion": events.addr(s)}
    C = C + [events.rec(C, coord, realize(C, lookups.load(C, o)))]
    return C + [events.spec_event(C, s)]


DEFECTS = [
    ("append-only (S1.1)", overwrite),
    ("shared order (S1.1)", stale_order),
    ("recorded inputs (S1.2)", hidden_draw),
    ("immutable versions (S1.3)", mutated_version),
    ("endogenous activation (S1.3)", exogenous_activation),
    ("retained evidence (S1.4)", lossy_evidence),
    ("certification (S1.5)", uncertified),
    ("record, then activate", activation_first),
]


def report(log=print):
    """Run the sound colony and the eight defective ones; returns [(condition, lost, first failure)]."""
    _, C = run("aco")
    sound = verify(C)
    log(f"sound mechanism: {len(C)} events, replay " + ("OK" if not sound else f"FAILS {sound[0]}"))
    out = []
    for k, (condition, defect) in enumerate(DEFECTS, 1):
        C = defect()
        failures = verify(C)
        first = failures[0] if failures else None
        what = lost(first[1]) if first else None               # read from the failed check, not asserted here
        out.append((condition, what, first))
        log(f"{k}  {condition}")
        log(f"   deviation  {defect.__doc__.split('. ', 1)[1]}")
        log(f"   replay     " + (f"stops at event {first[0]} of {len(C)}: {first[1][:110]}" if first else "finds nothing"))
        log(f"   lost       {what}")
    return out
