"""[R2] Deterministic verification replay from the record alone.     Paper: §4.2.6, Theorem B, Theorem C′

The replay uses only C: no service, no state of Z₀, no clock. For every event at position n it
re-derives the event from the prefix Cⁿ with the model (ztes.model) and reports the first check
that fails, named by the S1 condition it protects. By Theorem C′, a judgment-relevant violation
of S1 at an admitted event shows up here, at that event.
"""
from ..model import SpecError, judge, realize, types
from ..model.view import Record
from . import events, lookups
from .governance import refusal


# What each check protects (Table 5): the requirement that is lost when it fails.
LOST = (("S1.1 position", "R1"), ("S1.5 hash link", "R2"), ("genesis", "R1"),
        ("S1.3 specification address", "R2"), ("S1.3 specification not admissible", "R1"),
        ("S1.3 ontology version not active", "R1"), ("S1.3 criterion version not active", "R1"),
        ("S1.4 boundary", "R2"), ("S1.2/S1.4 realization", "R2"), ("S1.2 criterion is false", "R2"))


def lost(reason):
    """The requirement a failed check stands for: "R1" (governance) or "R2" (replay)."""
    for start, requirement in LOST:
        if reason.startswith(start):
            return requirement
    return "R2"                                                 # a specification that cannot be loaded or evaluated


def check(P, e):
    """Verify one event e against its prefix P = Cⁿ. Raises AssertionError on failure."""
    c = e["coord"]
    assert c["n"] == len(P), "S1.1 position in the shared order"
    assert c["prev"] == events.link(P), "S1.5 hash link to the preceding event"

    if c["kind"] == "genesis":
        assert len(P) == 0, "genesis must be the first event"

    elif c["kind"] == "spec":                                          # phases 1 and 2
        assert c["addr"] == events.addr(e["payload"]), "S1.3 specification address"
        why = refusal(P, e["payload"])
        assert why is None, f"S1.3 specification not admissible under τ_root: {why}"

    elif c["kind"] == "exec":                                          # phase 3
        a = c["abstraction"]
        assert c["ontology"] == lookups.active(P, a, "ontology"), "S1.3 ontology version not active in Cⁿ"
        assert c["criterion"] == lookups.active(P, a, "criterion"), "S1.3 criterion version not active in Cⁿ"
        o = lookups.load(P, c["ontology"])
        if o.get("boundary"):                                          # §5.2: the occurrence is the evidence
            w = realize(P, o, types.decode(o["returns"], e["payload"]))
            assert w == e["payload"], "S1.4 boundary occurrence does not have its declared type"
        else:
            w = realize(P, o)                                          # replay of 3a [ω]
            assert w == e["payload"], f"S1.2/S1.4 realization gives {w}, record has {e['payload']}"
        assert judge(P, lookups.load(P, c["criterion"]), w), "S1.2 criterion is false on replay"   # 3b [τ]

    else:
        raise AssertionError("unknown event kind")


def verify(C):
    """[R2] Replay the whole record; returns [(n, reason)] for every event that fails (empty: R2 holds)."""
    if not isinstance(C, Record):
        C = Record.of(C)                                       # one index for all prefixes
    errors = []
    for n, e in enumerate(C):
        try:
            check(C[:n], e)
        except (AssertionError, KeyError, SpecError) as x:
            errors.append((n, str(x)))
    return errors
