"""[τ] The eschatological axis: judgment Sτ of a candidate on a prefix of the record.   Paper: §3.4.1, D2

    Sτ : Dτ × Ω → 𝔹     total and Boolean

judge(C, s, w) is step 3b of an invocation: it reads κτ(C) (epistemic.project), adds the
candidate w under the name the criterion declares, evaluates the body, and returns exactly one
Boolean.

D2 (ontology–admission separation): the criterion is a separate specification with its own
inputs. It does not repeat the ontology; it checks what an admitted value must satisfy,
whatever produced the candidate. It is judged on the same prefix Cⁿ as the realization.

Totality is established before the criterion is recorded (validation.py: every binding that
could be missing has a default), so ⊥ cannot occur here; if it did, it would be a defect of
the specification and is reported as such.
"""
from . import types
from .epistemic import prepared, project
from .errors import SpecError, Undefined, where_of
from .language import evaluate
from .ontological import located


def judge(C, s, w):
    """[τ] Sτ on (C, ω): exactly one Boolean."""
    def run():
        env = project(C, s)
        candidate = s["inputs"]["candidate"]
        env[candidate["name"]] = types.decode(candidate["type"], w)
        return evaluate(s["body"], env, prepared(s).ns)
    try:
        r = located(s, run)
    except Undefined as x:                                     # excluded by validation: τ is total
        raise SpecError(f"{where_of(s)}: criterion is not total: {x}") from None
    if not isinstance(r, bool):
        raise SpecError(f"{where_of(s)}: criterion contract: the result must be a Boolean, got {r!r}")
    return r
