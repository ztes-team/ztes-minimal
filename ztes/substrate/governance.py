"""[Z₀] τ_root: the criterion that admits specifications.    Paper: §3.4.1 (Remark), §3.4.3, §4.2.7, S1.3, R1

Phases 1 and 2 are ordinary admissions under Axiom 0, and their criterion is τ_root. Every
change of a specification therefore passes through the same admission rule as execution:
governance is internal to execution (R1).

τ_root judges a specification s on the prefix Cⁿ. It has two parts:

    the API     s is a well-formed specification (model.validation.problems): independent of C
    the record  s continues its lineage in C:
                  - its version is the next one (versions 1, 2, … without gaps; immutable lineage);
                  - an ontology names the criterion that is active in Cⁿ: the eschatological
                    specification comes first, the ontological one is bound to it (§3.1.4, §3.4.3)

It checks the API, not the domain meaning: what an abstraction does is judged by its own
criterion in phase 3.
"""
from ..model import validation
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
