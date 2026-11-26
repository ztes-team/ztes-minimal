"""[Z₀] Phase 3 without a central agenda: one worker per abstraction.   Paper: §9.1.1, §5.1 (Lemma 6), §5.3

The agenda (agenda.py) executes phase 3 in one process: one instance of Z₀ invokes the
abstractions in turn. Here every abstraction is a worker with its own instance of Z₀. A worker
reads the record, applies Axiom 0 to its abstraction, and appends to the one shared record
itself. Nothing in a system changes: the same specifications and the same plan are executed,
and which of the two executes phase 3 is an option of the configuration (execution.mode).

What stays in one place, and why:

  * the order of C: every worker appends with the same conditional insert at position n, so
    one store decides the order (S1.1);
  * the plan: a coordinator records the specifications (phases 1 and 2), the governed changes
    and the KPI, with the workers paused, so that a regime changes as a whole;
  * termination: a worker that has nothing to add on Cⁿ says so; when all say it for the same
    n, and n is the length of C, no invocation can extend C: Terminal_r(C) holds. The result
    of a worker depends on Cⁿ alone, so this is established exactly and not by waiting.

A worker is its own agenda. After Not Yet or false it waits until an event appears in its
event horizon, or a specification of its own; events elsewhere cannot change its result
(Lemma 6) and do not wake it. For the same reason a worker that loses the race for position n
to an event outside its horizon appends the candidate it has at n + 1 (Z0._stands).

Axiom 0 does not fix the order in which abstractions are invoked, and here the order is
decided by a race, so two runs may give two records. Each is valid (R2). The history of an
abstraction whose result is determined by its inputs is the same in all of them (Theorem K),
and with it the "expect" of a system; the counts of the profile depend on the schedule.

This is one possible distribution of the execution, kept small; it is not the widest or the
fastest one. The appends form one order whatever the number of workers, so what runs in
parallel is the evaluation of ontologies and criteria.

A worker holds no state of its own: what it knows it reads from the record. A worker that
fails is started again and continues; the invocation it lost left no event, and the new one is
judged on the current prefix, so a failure is a delay and nothing else. (What is lost is the
count of its invocations that ended at Not Yet or false, which were never in C.)

Workers and coordinator tell each other how far they are through notes of the store
(store.py), which are not events: "control" (written by the coordinator) and "worker|<name>".
"""
import threading
import time
import uuid

from ..service import AbstractionService, ServiceUnavailable
from ..substrate import lookups
from ..substrate.governance import carried
from ..substrate.store import read
from ..substrate.z0 import ADMITTED, NOT_YET, Z0
from . import agenda, sources
from .report import _text

CONTROL = "control"


class Paused(Exception):
    """The step of the plan allows no further event; the invocation is kept for the next step."""


class Bounded:
    """The store as a worker uses it: no append at or beyond position `until` (a step of the plan
    that admits a given number of events, or the admission limit).
    """

    def __init__(self, store):
        """The store, with no bound until the coordinator sets one for a step."""
        self.store, self.until = store, None
        if hasattr(store, "get_many"):
            self.get_many, self.batch = store.get_many, store.batch

    def get(self, n):
        """The event at position n: reading is not bounded."""
        return self.store.get(n)

    def put_if_absent(self, n, event):
        """The insert of the store, refused with Paused at or beyond the bound of the current step."""
        if self.until is not None and n >= self.until:
            raise Paused()
        return self.store.put_if_absent(n, event)


class Worker:
    """One abstraction, executed by its own instance of Z₀ on the shared record."""

    def __init__(self, system, name, store, poll=0.002, hesitate=None):
        """hesitate: for tests, a function called before every invocation (e.g. a random pause)."""
        self.name, self.notes, self.poll, self.hesitate = name, store, poll, hesitate
        self.store = Bounded(store)
        self.z0 = Z0(self.store, {name: AbstractionService(self.store, name)})
        self.source = sources.make(system.declared_sources).get(name)    # a boundary abstraction (§5.2)
        self.occurrence = None                           # drawn for an invocation that has not ended yet
        self.last = (NOT_YET, None)
        self.seen, self.due, self.told = 0, True, None   # due: an invocation could change something
        # A worker keeps nothing that the record does not give back. Started on a record that
        # already holds events of its abstraction (after a failure), it takes them as admitted
        # and lets its source pass the occurrences they used; its first invocation is judged on
        # the prefix it finds, as that of any worker that was merely slow.
        own = sum(1 for e in read(self.store) if e["coord"]["kind"] == "exec" and e["coord"]["abstraction"] == name)
        self.outcomes = {"I": own, "A": own, "U": 0, "H": 0, "F": 0}
        for _ in range(own if self.source else 0):
            self.source.next()

    def run(self):
        """Step until the coordinator stops the run. A failure is written to the worker's note, where
        the coordinator finds it, and then raised.
        """
        try:
            while self.step():
                pass
        except Exception as x:                           # the coordinator stops the run and says why
            self.notes.put_note(f"worker|{self.name}", {"state": "failed", "error": f"{type(x).__name__}: {x}"})
            raise

    def step(self):
        """Look at the record once, and invoke the abstraction if that could add an event."""
        control = self.notes.get_note(CONTROL)
        if control is None or control.get("stop"):
            if control is None:
                time.sleep(self.poll)
            return control is None
        C = read(self.store)
        self.look(C)
        until = control.get("until")
        if not control["go"] or (until is not None and len(C) >= until):
            return self.tell(control, "paused", len(C))
        if not self.due:
            return self.tell(control, "idle", len(C))
        if self.hesitate:
            self.hesitate()
        if self.source and self.occurrence is None:
            self.occurrence = self.source.next()
        self.store.until = until
        try:
            result, w = self.z0.execute(self.name, self.occurrence)
        except Paused:
            return True
        n = self.z0.position                             # the prefix Cⁿ it was judged on
        agenda.count_outcome(self.outcomes, result, read(self.store, n), self.name)
        self.occurrence, self.last = None, (result, w)
        self.due = result == ADMITTED                    # its own event: evaluate again
        self.seen = n + 1 if result == ADMITTED else n
        return True

    def look(self, C):
        """Events appended since the last look: do they touch this abstraction?"""
        if len(C) > self.seen:
            watched = {self.name, *lookups.horizon(C, self.name)}
            if any(e["coord"].get("abstraction") in watched or any(d["abstraction"] == self.name for d in carried(e))
                   for e in C[self.seen:]):
                self.due = True                          # its horizon, or a specification of its own carried by another
            self.seen = len(C)

    def tell(self, control, state, n):
        """Report to the coordinator, once per change; then wait a moment."""
        told = (control["run"], control["step"], state, n)
        if told != self.told:
            self.notes.put_note(f"worker|{self.name}", {
                "run": control["run"], "step": control["step"], "state": state, "at": n,
                "outcomes": self.outcomes, "last": list(self.last)})
            self.told = told
        time.sleep(self.poll)
        return True


class Coordinator:
    """Executes a phase-3 step of the plan through the workers (the `phase3` of System.run)."""

    def __init__(self, store, poll=0.002, timeout=60.0, start=None):
        """A new run, with its own id; the workers are told to wait. start(name): start a worker for
        an abstraction that a carried specification brings into being; None when the workers run
        elsewhere, where its worker is started as every other (`python -m ztes work`).
        """
        self.store, self.poll, self.timeout, self.start = store, poll, timeout, start
        self.run, self.step, self.scanned = uuid.uuid4().hex, 0, 0
        self._control(go=False)

    def _adopt(self, system, C=None):
        """Adopt the abstractions that events of C (by default, the record as it is now) appended since
        the last look carry specifications of and the system does not have yet (System.adopt), and
        start a worker for each if the workers run here. From then on the coordinator waits for its
        report as for every other worker.
        """
        C = read(self.store) if C is None else C
        for e in C[self.scanned:]:
            for d in carried(e):
                if system.adopt(d["abstraction"]) and self.start is not None:
                    self.start(d["abstraction"])
        self.scanned = len(C)

    def _control(self, **fields):
        """Write the control note: the next step of this run, with the given fields (go, until, stop)."""
        self.step += 1
        self.store.put_note(CONTROL, {"run": self.run, "step": self.step, **fields})

    def _reports(self, system, accept, n):
        """The reports of all workers for the current step at length n of C, or None."""
        reports = {}
        for a in system.abstractions:
            r = self.store.get_note(f"worker|{a}")
            if r and r.get("state") == "failed":
                raise ServiceUnavailable(f"worker {a} failed: {r['error']}")
            if not r or (r["run"], r["step"], r["at"]) != (self.run, self.step, n) or not accept(r, n):
                return None
            reports[a] = r
        return reports

    def _wait(self, system, accept):
        """Wait until every worker reports as `accept` requires, at the current length of C; then return
        the reports. ServiceUnavailable after `timeout` seconds.
        """
        end = time.monotonic() + self.timeout
        while True:
            # One reading of C for both: the abstractions brought in by C are adopted, and every worker,
            # adopted ones included, must report at the length of that same C. Reading C twice would let
            # an event that brings in an abstraction fall between the two, and the run would be judged
            # terminal while the new abstraction has not yet been invoked.
            C = read(self.store)
            self._adopt(system, C)                       # an abstraction brought in since: its worker reports too
            reports = self._reports(system, accept, len(C))
            if reports is not None:
                return reports
            if time.monotonic() > end:
                raise ServiceUnavailable(f"the workers of {system.abstractions} did not all report within "
                                         f"{self.timeout} s (are they running, on this record?)")
            time.sleep(self.poll)

    def __call__(self, system, z0, max_admissions, log):
        """Execute one phase-3 step of the plan by the workers: let them run until each is idle on the
        same Cⁿ (terminal) or the bound of the step is reached, pause them, take their counts for the
        profile, and report.
        """
        start = len(z0.prefix())
        until = start + (max_admissions or system.admission_limit)
        self._control(go=True, until=until)
        # terminal: every worker has nothing to add on the same Cⁿ; or the step is used up
        self._wait(system, lambda r, n: r["state"] == "idle" or n >= until)
        self._control(go=False)                          # and no worker is inside an invocation
        reports = self._wait(system, lambda r, n: r["state"] == "paused")
        C = read(self.store)
        for e in C[start:]:
            log(f"   C^{e['coord']['n']:<3} {e['coord']['abstraction']:12} → admitted   ω = {_text(e['payload'])}")
        for a, r in reports.items():
            system.outcomes[a], system.last[a] = r["outcomes"], tuple(r["last"])
        if len(C) < until:
            agenda.termination_report(system, C, log)
        elif max_admissions:
            log(f"   paused after {len(C) - start} admissions")
        else:
            log(f"   stopped at the admission limit {system.admission_limit}: not terminal")

    def stop(self):
        """Tell every worker to stop."""
        self._control(go=False, stop=True)


def run(system, store, local=True, poll=0.002, timeout=60.0, log=print, plan=None, hesitate=None):
    """Execute the plan with one worker per abstraction. Returns the instance of Z₀ of the coordinator.

    local: the workers are threads of this process, each with its own handle on the record;
           otherwise they are expected to run elsewhere (`python -m ztes work SYSTEM ABSTRACTION`).
    """
    threads = []

    def start(a):
        """A worker for abstraction a, in a thread of this process."""
        worker = Worker(system, a, store.again(), poll, hesitate)
        threads.append(threading.Thread(target=worker.run, name=f"worker {a}", daemon=True))
        threads[-1].start()

    coordinator = Coordinator(store, poll, timeout, start if local else None)
    if local:
        for a in system.abstractions:
            start(a)
    try:
        log(f"Workers  phase 3 is executed by {len(system.abstractions)} workers, one per abstraction"
            + ("" if local else " (running elsewhere)"))
        return system.run(store, log=log, plan=plan, phase3=coordinator)
    finally:
        coordinator.stop()
        for t in threads:
            t.join(timeout=5)
