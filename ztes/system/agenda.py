"""[Z₀] Phase 3: the agenda, termination, and the state of each abstraction.   Paper: §4.1.3, §4.6.5, §6.3

Phase 3 is driven by an agenda, as in a three-phase simulation: after each
admission only the abstractions that can be affected are evaluated again.

  * At the start every abstraction is on the agenda.
  * Z₀ takes one abstraction from the agenda and applies Axiom 0. For a boundary abstraction
    with a declared source (sources.py) the invocation is bound to the next occurrence.
  * admitted:        the abstraction itself and every abstraction whose event
                     horizon contains it go back on the agenda; so does every abstraction
                     whose specification the event carries (governance.py), and one that
                     the system did not have is adopted (System.adopt);
  * Not Yet / false: the abstraction leaves the agenda and waits. Not Yet (ω = ⊥) has two
                     grounds, counted separately: the horizon is incomplete (an event the
                     ontology requires is not in Cⁿ; nothing is computed), or the horizon is
                     complete and the body, computed on it, yields no candidate. false is
                     the third ground: ω exists and τ refuses it on this prefix. Its result is a
                     function of the events in its horizon and of its active
                     specifications only, so it can change only when one of those
                     lineages gains an event, or when a governed change gives it a
                     new specification (which puts it back on the agenda).
  * The agenda is empty: no abstraction generates events and no abstraction waits
    for an event that can still occur in its horizon. No active invocation can
    extend C, i.e. Terminal_r(C) holds (§4.6.5). Because every body is a
    terminating expression over declared inputs, this is established exactly,
    not estimated by waiting.

At termination every abstraction is in one of two states:

  * closed:          ω exists but τ is false (a goal reached, or a protective condition);
  * permanent wait:  Not Yet, and nothing in its horizon can still change in this
                     regime; if the horizon names a lineage outside the system
                     (an external abstraction), the wait is on that lineage.

A governed change starts a new regime: the changed abstraction is put back on the
agenda and execution continues at the next phase-3 step of the plan.
"""
from ..model import explain as explaining
from ..model import missing
from ..substrate import lookups
from ..substrate.governance import carried
from ..substrate.store import read
from ..substrate.z0 import ADMITTED, FALSE, NOT_YET
from .report import _text

OUTCOME = {ADMITTED: "A", NOT_YET: "U", FALSE: "F"}        # the three outcomes of Axiom 0


def dependents(system, C, a):
    """Abstractions whose event horizon contains a: they may change when a is admitted (Definition 10)."""
    return [b for b in system.abstractions if a in lookups.horizon(C, b)]


def execute(system, z0, max_admissions, log):
    """Phase 3: run the agenda until it is empty (terminal) or max_admissions is reached."""
    admitted = 0
    limit = max_admissions or system.admission_limit
    while system.agenda and admitted < limit:
        a = system.agenda.pop(0)
        source = system.sources.get(a)                   # a boundary abstraction: the occurrence (§5.2)
        result, w = z0.execute(a, source.next() if source else None)
        n = z0.position                                  # the prefix Cⁿ it was judged on
        system.last[a] = (result, w)
        count_outcome(system.outcomes[a], result, read(z0.store, n), a)
        log(f"   C^{n:<3} {a:12} → {result}" + (f"   ω = {_text(w)}" if w is not None else ""))
        if system.trace:
            for line in explain_invocation(system, read(z0.store, n), a, w):
                log("        " + line)
        if result == ADMITTED:
            admitted += 1
            C = read(z0.store, n + 1)                    # Cⁿ⁺¹: the new event
            changed = [d["abstraction"] for d in carried(C[n])]   # abstractions whose specifications it carries
            for b in changed:
                system.adopt(b, z0)                      # one that is new here exists from now on
            for b in [a] + dependents(system, C, a) + changed:
                if b not in system.agenda:
                    system.agenda.append(b)
    if system.agenda and max_admissions:
        log(f"   paused after {admitted} admissions; agenda {system.agenda}")
    elif system.agenda:
        log(f"   stopped at the admission limit {system.admission_limit}: not terminal"
            " (raise \"admission_limit\" in system.json if the system needs more)")
    else:
        termination_report(system, z0.prefix(), log)


def count_outcome(count, result, P, a):
    """Bookkeeping for the profile (kpi.py): one invocation of a, judged on the prefix P."""
    if result in OUTCOME:
        count["I"] += 1
        count[OUTCOME[result]] += 1
        if result == NOT_YET and waits_on_horizon(P, a):
            count["H"] += 1                              # ⊥ decided by the horizon alone


def waits_on_horizon(P, a):
    """Was this Not Yet decided by the horizon alone: an event the active ontology needs is not in P?"""
    s = lookups.load(P, lookups.active(P, a, "ontology"))
    return bool(s.get("boundary")) or missing(P, s) is not None


def explain_invocation(system, P, a, w):
    """The evaluation of one invocation on its prefix P, step by step."""
    o, c = lookups.active(P, a, "ontology"), lookups.active(P, a, "criterion")
    if o is None or c is None:
        return ["(specifications not yet recorded)"]
    lines = explaining.explain(P, lookups.load(P, o))
    if w is not None:
        lines += explaining.explain(P, lookups.load(P, c), w)
    return lines


def termination_report(system, C, log=print):
    """Terminal_r(C): no active invocation can extend C. State of every abstraction."""
    log("   terminal: no abstraction can extend C in this regime")
    for a in system.abstractions:
        result, w = system.last.get(a, (NOT_YET, None))
        if result == FALSE:
            log(f"     {a:12} closed: ω = {_text(w)}, τ false")
        else:
            external = [b for b in lookups.horizon(C, a) if b not in system.abstractions]
            where = f"waits on external {external}" if external else "its horizon is quiescent"
            log(f"     {a:12} permanent wait (Not Yet): {where}")


def states(system, C):
    """Termination states as data: abstraction → "closed" | "wait" | "wait-external"."""
    out = {}
    for a in system.abstractions:
        result, _ = system.last.get(a, (NOT_YET, None))
        if result == FALSE:
            out[a] = "closed"
        else:
            out[a] = "wait-external" if any(b not in system.abstractions
                                            for b in lookups.horizon(C, a)) else "wait"
    return out
