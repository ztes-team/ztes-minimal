"""[Z₀][C] Events and the deterministic recording function Rec.     Paper: §3.2.5, S1.2, S1.4, S1.5

An event has two logical fields, e = ⟨coord(e), payload(e)⟩ (§3.2.5, §9.1).

    coord    where the event stands and what produced it: position n, kind,
             abstraction, addresses of the specification versions used,
             and the hash of the preceding event
    payload  the admitted content: a specification (phases 1 and 2)
             or a realized candidate ω (phase 3)

Rec is deterministic (S1.2): the same prefix, invocation and payload always
give the same event. The hash link `prev` makes the record self-certifying
(S1.5): changing any admitted event breaks the link of the next one, and
together with the retained specifications it keeps the evidence that R2
needs (S1.4).
"""
import hashlib

from ..model.types import canon

GENESIS = "0" * 64


def addr(x):
    """Content address of a specification or an event (immutable addressing, S1.3)."""
    return hashlib.sha256(canon(x).encode()).hexdigest()


def link(C):
    """Hash of the last event of the prefix C (S1.5), computed from the event itself."""
    return addr(C[-1]) if C else GENESIS


def rec(C, coord, payload, prev=None):
    """Rec(i, C^n, payload): the unique event that may be appended at position n = |C|.

    prev: the hash of the last event of C when the caller already has it (store.read keeps it).
    """
    return {"coord": {"n": len(C), **coord, "prev": link(C) if prev is None else prev}, "payload": payload}


# --- the three kinds of events -------------------------------------------------

def genesis():
    """C^0 → C^1: the fixed starting event of Z₀; τ_root is the first registered criterion."""
    return rec([], {"kind": "genesis"}, "tau_root v1")


def spec_event(C, s, prev=None):
    """Phases 1 and 2: the payload is a specification; its address is part of the coordinate."""
    coord = {"kind": "spec", "abstraction": s["abstraction"], "role": s["role"],
             "version": s["version"], "addr": addr(s)}
    return rec(C, coord, s, prev)


def exec_event(C, name, ontology_addr, criterion_addr, omega, prev=None):
    """Phase 3: the payload is ω; the coordinate names the exact versions that produced and judged it."""
    coord = {"kind": "exec", "abstraction": name,
             "ontology": ontology_addr, "criterion": criterion_addr}
    return rec(C, coord, omega, prev)
