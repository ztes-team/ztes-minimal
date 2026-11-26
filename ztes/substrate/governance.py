"""[Z₀] τ_root: the criterion that admits specifications.    Paper: §3.4.1 (Remark), §3.4.3, §4.2.7, S1.3, R1

Phases 1 and 2 are ordinary admissions under Axiom 0, and their criterion is τ_root. Every
change of a specification therefore passes through the same admission rule as execution:
governance is internal to execution (R1).

τ_root judges a specification s on the prefix Cⁿ. It has two parts:

    the API     s is a well-formed specification (model.validation.problems): independent of C
    the record  s continues its lineage in C:
                  - its version is the next one (versions 1, 2, … without gaps; immutable lineage);
                  - an ontology names the criterion that is active in Cⁿ: the eschatological
                    specification comes first, the ontological one is bound to it (§3.1.2, §3.4.3)

It checks the API, not the domain meaning: what an abstraction does is judged by its own
criterion in phase 3.

A specification enters C in one of two ways, judged by the same τ_root (R1):

    from a file    the plan records it as a specification event (phases 1 and 2, `govern`);
    in execution   a candidate of any abstraction carries it, in the one field of its type
                   {"list": "specification"} (model.types.carried_field). The criterion of that
                   abstraction, active in Cⁿ, judges the whole candidate: it is the authority in
                   force. Then τ_root judges each carried specification in order, each on Cⁿ
                   extended by the ones before it, so that a criterion and the ontology bound to it
                   may be carried together. If τ_root refuses one, the candidate is refused and
                   nothing is appended; if not, one execution event is appended, whose coordinate
                   lists what it carries, and every carried specification is active from that
                   event on (S1.3). Z₀ knows no kinds of abstraction: who may change what is a
                   question for criteria, not for Z₀.

A carried ontology is bound by Z₀ to the criterion active at its place in the order, as the plan
binds an ontology in phase 2: its proposer cannot know the address of a criterion, and need not.
"""
from ..model import types, validation
from . import events
from .lookups import active, specs


def refusal(C, s):
    """Why τ_root refuses s on C, as text; None if s is admissible."""
    found = validation.problems(s)
    if found:
        return "; ".join(found)
    a, role, v = s["abstraction"], s["role"], s["version"]
    expected = len(specs(C, a, role)) + 1
    if v != expected:
        return f"version {v}: the next version of {a}/{role} is {expected}"
    if role == "ontology":
        current = active(C, a, "criterion")
        if current is None:
            return "phase 2 requires phase 1: no criterion of this abstraction is recorded"
        if s["criterion"] != current:
            return f"lineage: bound to criterion {s['criterion']}, but the active criterion is {current}"
    return None


def tau_root(C, s):
    """[Z₀] τ_root(Cⁿ, s): true if and only if s may be recorded at position n."""
    return refusal(C, s) is None


# ---- specifications carried by a candidate ----

def _bound(C, carried):
    """The carried specifications with every ontology bound to the criterion of its abstraction that
    is active at its place: the last criterion carried before it in the same candidate, otherwise
    the one active in C. One whose abstraction is not a name is left as it is: τ_root refuses it.
    """
    out, latest = [], {}
    for s in carried:
        s, a = dict(s), s.get("abstraction")
        if isinstance(a, str) and s.get("role") == "criterion":
            latest[a] = events.addr(s)
        elif isinstance(a, str) and s.get("role") == "ontology":
            s["criterion"] = latest[a] if a in latest else active(C, a, "criterion")
        out.append(s)
    return out


def carried_refusal(C, carried):
    """Why τ_root refuses one of the carried specifications, judged in order, each on C extended by
    the ones before it; None if it admits them all. The rules are those of refusal(): a well-formed
    specification, the next version of its lineage, an ontology bound to the active criterion.
    """
    earlier, latest = {}, {}
    for k, s in enumerate(carried):
        found = validation.problems(s)
        if found:
            return f"carried specification {k}: " + "; ".join(found)
        a, role, v = s["abstraction"], s["role"], s["version"]
        expected = len(specs(C, a, role)) + earlier.get((a, role), 0) + 1
        if v != expected:
            return f"carried specification {k}: version {v}: the next version of {a}/{role} is {expected}"
        if role == "ontology":
            current = latest[a] if a in latest else active(C, a, "criterion")
            if current is None:
                return f"carried specification {k}: no criterion of {a} is recorded or carried before it"
            if s["criterion"] != current:
                return f"carried specification {k}: lineage: bound to criterion {s['criterion']}, but the active criterion is {current}"
        else:
            latest[a] = events.addr(s)
        earlier[(a, role)] = earlier.get((a, role), 0) + 1
    return None


def carry(C, ontology, w, bind=True):
    """What a candidate w of an abstraction with this active ontology carries on C.

    Returns (w, carries, why): w with its carried ontologies bound (the candidate that is judged
    and recorded); carries, the coordinate of what it carries ({"field", "specs": [{abstraction,
    role, version, addr}]}), or None if it carries nothing; why, the reason τ_root refuses a
    carried specification, or None. Without a carried field, or with an empty one, w is returned
    as it is.

    bind=False judges the carried specifications as they are, without binding them first: replay
    uses it on a recorded candidate, whose carried ontologies must already be bound to the right
    criterion (the lineage rule of carried_refusal).
    """
    field = types.carried_field(ontology.get("returns"))
    if field is None or not isinstance(w, dict) or not w.get(field):
        return w, None, None
    bound = _bound(C, w[field]) if bind else w[field]
    w = {**w, field: bound}
    why = carried_refusal(C, bound)
    carries = None if why else {"field": field, "specs": [
        {"abstraction": s["abstraction"], "role": s["role"], "version": s["version"], "addr": events.addr(s)}
        for s in bound]}
    return w, carries, why


def carried(e):
    """The descriptions {abstraction, role, version, addr} of the specifications an event carries."""
    c = e["coord"].get("carries")
    return c["specs"] if c else []

