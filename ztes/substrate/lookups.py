"""[Z₀][C] Specifications in the record: admitted versions, the active one, horizons.   Paper: S1.3, Def. 10

A specification exists for execution only once its event is admitted, and the active version
of a specification is the last one admitted (S1.3). The event horizon of an abstraction is the
set of lineages its active specifications read (Definition 10, §5.1). These are rules of Z₀
about C; the model only declares what a specification reads (model.epistemic.lineages).
"""
from ..model.epistemic import lineages
from ..model.view import indexed


def specs(C, abstraction, role):
    """Addresses of all admitted versions of one specification in C, in record order."""
    return indexed(C).version_addrs(abstraction, role, len(C))


def active(C, abstraction, role):
    """[S1.3] The active version is the last one admitted in C; None if there is none yet."""
    s = specs(C, abstraction, role)
    return s[-1] if s else None


def load(C, address):
    """Load a specification by address. It exists for execution only if it was admitted in C."""
    s = indexed(C).spec(address, len(C))
    if s is None:
        raise KeyError(f"specification {address} is not in the record")
    return s


def horizon(C, abstraction):
    """[Definition 10] The event horizon of an abstraction under its active specifications.

    Computed once per pair of active versions and kept in the index of the record.
    """
    ix = indexed(C)
    versions = (abstraction, active(C, abstraction, "ontology"), active(C, abstraction, "criterion"))
    h = ix.memo.get(("horizon",) + versions)
    if h is None:
        h = []
        for address in versions[1:]:
            if address:
                h += [a for a in lineages(load(C, address)) if a not in h]
        h = ix.memo[("horizon",) + versions] = tuple(h)
    return list(h)
