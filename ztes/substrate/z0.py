"""[Z₀] The zero-tier execution substrate: Axiom 0, the only writer to C.   Paper: §3.4.1, §3.4.3, §9.1.1, [50]

Z₀ is the fixed, domain-independent procedure that applies Axiom 0 over C. It is the zeroth
tier, presupposed rather than admitted, below every abstraction (§3.4.1: Axiom 0 is "the only
governing element presupposed rather than admitted"); its name follows the Zero Tier Execution
Substrate (ZTES) of the research program [50]. All domain content is in the specifications,
which are data in C and are evaluated by the model (ztes.model), never by Z₀ itself.

    phase 1   admit_criterion(Sτ)    [τ] record the admission API     (no evaluation)
    phase 2   admit_ontology(Sω)     [ω] record the mapping API       (no evaluation)
    phase 3   execute(name)          one invocation of Axiom 0:
                3a  ω := Sω(Cⁿ)                  ⊥ → Not Yet, nothing appended       [ω] D1
                3b  b := Sτ(Cⁿ, ω)               false → nothing appended           [τ] D2
                3c  Cⁿ⁺¹ := Cⁿ ⁀ Rec(i, Cⁿ, ω)   only if b is true: atomic append   [C] S1.1, S1.5

The three-step constitution of an abstraction in §3.4.3 (eschatological specification →
ontological specification → execution event) is phases 1, 2, 3; the factorization inside one
invocation is 3a, 3b, 3c.

Steps 3a and 3b are asked of the abstraction's service (ztes.service), which evaluates its
specifications on Cⁿ, in process or over HTTP. Only Z₀ appends to C.
"""
from . import events, lookups
from .governance import tau_root
from .store import known, read, tip, wrote

ADMITTED, FALSE, NOT_YET, UNSPECIFIED = "admitted", "false", "Not Yet", "unspecified"


class Z0:
    """Z₀ over one store. Several instances may share a store: the atomic insert keeps C one order."""

    def __init__(self, store, services):
        """services: abstraction name → service with realize(address, n[, occurrence]) and judge(address, n, ω)."""
        self.store, self.services = store, services
        self.position = None                                   # n of the prefix Cⁿ of the last invocation
        self.store.put_if_absent(0, events.genesis())          # C¹ = ⟨genesis⟩, idempotent

    def prefix(self):
        """The record as this instance has it."""
        return self._latest()

    # ---- phases 1 and 2: specifications admitted under τ_root ----

    def _latest(self, C=None):
        """The prefix to judge on. Without C: what this instance already has (all of it, the first
        time). With C: the store is asked whether the record has grown beyond C; None if not.

        A judgment on a prefix that is no longer the latest can do no harm: the append at
        position n fails and the invocation is judged again. Only an outcome that appends
        nothing (Not Yet, false) must be confirmed on the latest prefix before it is reported,
        and that costs one request.
        """
        if C is None:
            return known(self.store) or read(self.store)
        if self.store.get(len(C)) is None:                     # one key: is position n still free?
            return None
        return read(self.store)

    def _admit_specification(self, s):
        C = self._latest()
        while True:
            if not tau_root(C, s):                              # judgment on Cⁿ
                C2 = self._latest(C)
                if C2 is None:
                    return FALSE
                C = C2
                continue
            event = events.spec_event(C, s, tip(self.store, C))
            if self.store.put_if_absent(len(C), event):
                wrote(self.store, len(C), event)
                return ADMITTED                                 # recorded, hence active (S1.3)
            C = read(self.store)                                # position n was taken: judge again on Cⁿ⁺¹

    def admit_criterion(self, s):
        """Phase 1 [τ]: record the criterion API Sτ of an abstraction."""
        assert s["role"] == "criterion"
        return self._admit_specification(s)

    def admit_ontology(self, s):
        """Phase 2 [ω]: record the ontology API Sω; its lineage must name the active criterion."""
        assert s["role"] == "ontology"
        return self._admit_specification(s)

    # ---- phase 3: execution, one invocation of Axiom 0 ----

    @staticmethod
    def _stands(C, newer, name):
        """Does a judgment of `name` made on C hold on the longer prefix `newer`?   (Lemma 6)

        ω and τ read C only through the event horizon of the abstraction and through its active
        versions. If none of the events added since is an event of a lineage in that horizon,
        of the abstraction itself, or a specification of it, both are the same on `newer`, and the
        candidate may be appended there without being computed again. Replay agrees: on the
        prefix where the event stands it derives the same candidate and the same judgment.
        """
        watched = {name, *lookups.horizon(C, name)}
        return all(e["coord"].get("abstraction") not in watched for e in newer[len(C):])

    def execute(self, name, occurrence=None):
        """[A0] One invocation of abstraction `name`. Returns (result, ω).

        occurrence: for a boundary abstraction (§5.2), the occurrence bound to this invocation;
        its realization is that occurrence rather than a value computed from C. It is judged by
        the criterion like any candidate and, once admitted, retained in C as evidence (S1.4).
        """
        service = self.services[name]
        C = self._latest()
        while True:
            n = self.position = len(C)
            w_addr = lookups.active(C, name, "ontology")       # versions active in Cⁿ (S1.3)
            t_addr = lookups.active(C, name, "criterion")
            omega, result = None, UNSPECIFIED                  # phases 1 and 2 not yet done
            if w_addr is not None and t_addr is not None:
                omega = (service.realize(w_addr, n) if occurrence is None  # 3a [ω] realization on Cⁿ (D1)
                         else service.realize(w_addr, n, occurrence))
                if omega is None:
                    result = NOT_YET                           #    ⊥: τ is not called, nothing appended
                elif not service.judge(t_addr, n, omega):      # 3b [τ] judgment on the same Cⁿ  (D2)
                    result = FALSE                             #    false: nothing appended
                else:
                    while True:
                        event = events.exec_event(C, name, w_addr, t_addr, omega, tip(self.store, C))
                        if self.store.put_if_absent(n, event): # 3c [C] atomic append at position n
                            wrote(self.store, n, event)
                            return ADMITTED, omega
                        newer = read(self.store)               # another instance wrote position n first
                        stands = self._stands(C, newer, name)
                        C, n = newer, len(newer)
                        self.position = n
                        if not stands:
                            break                              # its horizon changed: judge again on the new prefix
                    continue
            newer = self._latest(C)                            # nothing appended: was Cⁿ the latest prefix?
            if newer is None:
                return result, (omega if result == FALSE else None)
            C = newer
