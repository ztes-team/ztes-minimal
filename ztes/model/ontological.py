"""[ω] The ontological axis: realization Sω on a prefix of the record.     Paper: §3.4.1, §3.2.4, D1

    Sω : Dω ⇀ Ω        partial and single-valued

realize(C, s) is step 3a of an invocation: it reads κω(C) (epistemic.project), evaluates the
body of the ontology s, and returns the encoded candidate ω, or None for ⊥.

⊥ is not a third value but partiality: the realization is undefined in this context. It arises
when the body returns None, or when a required binding has no event yet, i.e. the abstraction
waits for an event in its horizon. Z₀ reads ⊥ as Not Yet: the criterion is not called and
nothing is appended.

D1 (contextual ontological resolution): the candidate is determined by the context C. When the
relation that an abstraction lifts is multivalued, the body resolves it by a fixed rule over
the record; no selector chooses among the values.

A boundary abstraction (§5.2; specification field "boundary": true) is the one exception: its
candidate is not computed from C but is an occurrence bound to the invocation (an observation of
the environment or of the execution). realize then only checks that the occurrence has the
declared type; the criterion judges it as any candidate, and once admitted it is retained in C
as evidence (S1.4), so that R2 replays the judgment, not the observation.
"""
from . import types
from .epistemic import prepared, project
from .errors import SpecError, Undefined, where_of
from .language import evaluate


def located(s, f):
    """Run f; turn any failure other than ⊥ into a SpecError that names the specification."""
    try:
        return f()
    except Undefined:
        raise
    except SpecError as x:
        raise SpecError(f"{where_of(s)}, {x}") from None
    except Exception as x:
        raise SpecError(f"{where_of(s)}: {type(x).__name__}: {x}") from None


def realize(C, s, occurrence=None):
    """[ω] Sω on C: the encoded candidate ω, or None (⊥) when Sω is undefined in this context.

    For a boundary abstraction, ω is the occurrence bound to the invocation (None: ⊥).
    """
    if s.get("boundary"):
        return None if occurrence is None else located(s, lambda: types.encode(s["returns"], occurrence))
    try:
        r = located(s, lambda: evaluate(s["body"], project(C, s), prepared(s).ns))
    except Undefined:
        return None                                            # ⊥: Not Yet
    # the contract of Sω: ω has the declared type ("returns")
    return None if r is None else located(s, lambda: types.encode(s["returns"], r))
