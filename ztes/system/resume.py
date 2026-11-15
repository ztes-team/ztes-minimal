"""Starting a plan again on a record that already exists.                 Paper: Principle R (§5.3), R2

A run can be interrupted at any event: the append is atomic, so C is always a valid prefix. What
is lost with the process is the state of the scheduler: the agenda, the position of each source,
the counts of invocations that ended at Not Yet or false. None of it is in C, and none of it needs
to be: the schedule is a deterministic function of the plan and of the outcomes, so it is walked
again from the start, against the record.

Walk stands in for Z₀ while events of the record remain. Each invocation is evaluated on the
prefix it was originally judged on; where Z₀ would append, the next recorded event must be exactly
that event, and the walk moves past it. Nothing is written. When the record is exhausted the
scheduler is in the state it had at the interruption, and Z₀ itself continues.

A record that does not follow the plan (another system, another version of the tooling) is
reported at the first event that differs; it is never extended.
"""
from ..substrate import events, lookups
from ..substrate.store import read
from ..substrate.z0 import ADMITTED, FALSE, NOT_YET, UNSPECIFIED


class DifferentRecord(Exception):
    """The record in the store was not written by this plan: it cannot be continued by it."""


class Walk:
    """Z₀'s interface over an existing record: walks it while it lasts, then hands over to Z₀."""

    def __init__(self, z0):
        self.z0, self.store, self.services = z0, z0.store, z0.services
        self.n, self.end = 1, len(read(z0.store))              # position 0 is genesis
        self.position = None

    @property
    def walking(self):
        return self.n < self.end

    def prefix(self):
        """The record as the scheduler sees it now: the prefix walked so far, then all of C."""
        return read(self.store, self.n) if self.walking else self.z0.prefix()

    def _expect(self, event, what):
        there = read(self.store, self.n + 1)[self.n]
        if there != event:
            c = there["coord"]
            raise DifferentRecord(f"event {self.n} of the record is {c['kind']} {c.get('abstraction', '')}, "
                                  f"but this plan would record {what} there")
        self.n += 1

    def _admit(self, s, live):
        if not self.walking:
            return live(s)
        P = self.prefix()
        self._expect(events.spec_event(P, s), f"{s['abstraction']}/{s['role']}.v{s['version']}")
        return "recorded"

    def admit_criterion(self, s):
        return self._admit(s, self.z0.admit_criterion)

    def admit_ontology(self, s):
        return self._admit(s, self.z0.admit_ontology)

    def execute(self, name, occurrence=None):
        if not self.walking:
            result = self.z0.execute(name, occurrence)
            self.position = self.z0.position
            return result
        P, n = self.prefix(), self.n
        self.position = n
        w_addr, t_addr = lookups.active(P, name, "ontology"), lookups.active(P, name, "criterion")
        if w_addr is None or t_addr is None:
            return UNSPECIFIED, None
        service = self.services[name]
        omega = service.realize(w_addr, n) if occurrence is None else service.realize(w_addr, n, occurrence)
        if omega is None:
            return NOT_YET, None
        if not service.judge(t_addr, n, omega):
            return FALSE, omega
        self._expect(events.exec_event(P, name, w_addr, t_addr, omega), f"an event of {name}")
        return ADMITTED, omega
