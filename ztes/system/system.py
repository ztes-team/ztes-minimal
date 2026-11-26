"""A system of abstractions given in a standard form, and the execution of its plan by Z₀.

A system is a directory:

    system.json                      name, title, abstractions, plan, expect; shared declarations
    DESIGN.md                        step 0: the design, for the reader
    abstractions/<name>/abstraction.json       optional shared declarations of one abstraction
    abstractions/<name>/criterion.v<k>.json    Sτ versions   (phase 1, governed changes)
    abstractions/<name>/ontology.v<k>.json     Sω versions   (phase 2, governed changes)

Specification files are written in the short authoring format and expanded into
complete specifications when the system is loaded (authoring.py).

The plan is a list of steps executed in order:

    {"phase": 1}                          record criterion v1 of every abstraction
    {"phase": 2}                          record ontology v1 of every abstraction, bound to its criterion
    {"phase": 3}                          execute until the system is terminal
    {"phase": 3, "max_admissions": k}     execute at most k admissions, then continue with the plan
    {"govern": ["a/criterion.v2", …]}     record new specification versions (governed change, §4.2.7)

A new version may also be carried by a candidate in phase 3 (substrate/governance.py): it is then
recorded by its execution event, and an abstraction the system did not have is adopted (adopt).
    {"kpi": true}                         compute the execution indicators now (kpi.py): profile, then
                                          the system's own KPI abstraction ("kpi" in system.json)

"sources" names, for a boundary abstraction (§5.2), where its occurrences come from during phase 3
(sources.py), e.g. {"draw": {"random": {"seed": 1, "size": 11, "below": 1000000}}}.

Without a plan the default is phase 1, phase 2, phase 3 until terminal.

Phase 3 is executed by the agenda of one process (agenda.py) or, as an option of the
configuration, by one worker per abstraction (workers.py). The plan is the same in both.

"admission_limit" (default 10000) bounds one phase-3 step, as a guard against criteria
that never close.

"expect" states the expected end, checked after the run (check_expect):
    {"events": 23, "states": {"a": "closed", …}, "values": {"a": [payload, …], …}}
Neither the model nor Z₀ contains domain content: everything specific to a system is in its files.
"""
from pathlib import Path

from ..service import AbstractionService
from ..substrate import lookups
from ..substrate.store import read
from ..substrate.z0 import Z0
from . import agenda, checks, kpi, sources
from .authoring import load_specs, read_directory, write_directory
from .resume import Walk

DEFAULT_PLAN = [{"phase": 1}, {"phase": 2}, {"phase": 3}]

ADMISSION_LIMIT = 10_000          # guard against criteria that never close (non-convergence, §4.6.5)


class System:
    """A system of abstractions (step 0: the result of design).

    System(path)                 load a system stored as a directory (the standard form)
    System.from_dict(definition) build it from a definition made in code (see authoring.py)
    system.save(path)            store it as a directory in the standard form
    """

    def __init__(self, path=None, definition=None):
        """Load a system from its directory (path) or from a definition already read (a dict, as
        authoring.read_directory gives it), and expand every specification into its recorded form.
        Nothing is recorded: that is what run() does.
        """
        assert (path is None) != (definition is None), "give a directory or a definition"
        self.path = Path(path) if path is not None else None
        m = read_directory(self.path) if path is not None else definition
        self.definition = m
        self.name, self.title = m["system"], m.get("title", m["system"])
        self.declared = list(m["abstractions"])               # the domain abstractions of the files
        self.abstractions = list(self.declared)               # and those a run adopts (adopt)
        self.kpi = m.get("kpi")                                # optional KPI abstraction of this system
        self.declared_sources = m.get("sources", {})           # occurrences for boundary abstractions
        self.plan = m.get("plan", DEFAULT_PLAN)
        self.expect = m.get("expect")
        self.admission_limit = m.get("admission_limit", ADMISSION_LIMIT)
        # "a/role.vk" → complete specification, expanded from the authoring format (not yet active)
        self.specs = load_specs({**m, "types": {**kpi.KPI_TYPES, **m.get("types", {})},
                                 "bindings": {**kpi.KPI_BINDINGS, **m.get("bindings", {})}})
        self.specs.update(kpi.profile_specs(self.abstractions))   # generated: KPI above Z₀
        for a in self.abstractions + ([self.kpi] if self.kpi else []):
            for required in ("criterion.v1", "ontology.v1"):
                assert f"{a}/{required}" in self.specs, f"abstraction {a} has no {required}.json"

    @classmethod
    def from_dict(cls, definition):
        """A system from a definition already read (see __init__)."""
        return cls(definition=definition)

    def save(self, path, design=None):
        """Store the system as a directory; returns the System loaded from there."""
        write_directory(self.definition, path, design)
        return System(path)

    # ---- step 0 -----------------------------------------------------------------

    def describe(self, log=print):
        """Print step 0: every specification of the system, with its horizon and the form of its body."""
        log(f"Step 0  design: {self.title}")
        for key, s in self.specs.items():
            b = s.get("body")
            shown = ("boundary: the occurrence of the invocation" if b is None else
                     f"function {b.split('(')[0].split()[-1]}(…)" if isinstance(b, str) else f"result = {b['result']}")
            log(f"   {key:22} horizon {lookups.lineages(s)}  {shown}")

    def check(self, log=print):
        """The static check of the system (checks.py). Returns a list of problems."""
        return checks.check(self, log)

    def states(self, C):
        """The final state of every abstraction (agenda.py)."""
        return agenda.states(self, C)


    # ---- services ---------------------------------------------------------------------

    def all_abstractions(self):
        """The domain abstractions and the KPI abstractions above them (profile, and kpi if declared)."""
        return self.abstractions + [kpi.PROFILE] + ([self.kpi] if self.kpi else [])

    def services(self, store, http=False, base_port=8701, wait=0.0, client=None, startup=1.0):
        """One microservice per abstraction: in-process, or HTTP (FastAPI) in background threads.

        store: what the services read (the record's store, or a replica of it); wait: how long
        a service waits until that store holds Cⁿ; client: url → the client Z₀ calls it with.
        The settings come from ztes.yaml (config.open_services).
        """
        if not http:
            return {a: AbstractionService(store, a, wait) for a in self.all_abstractions()}
        import threading, time, uvicorn
        from ..service import HttpService, make_app
        clients = {}
        for i, a in enumerate(self.all_abstractions()):
            cfg = uvicorn.Config(make_app(store, a, wait), port=base_port + i, log_level="warning")
            threading.Thread(target=uvicorn.Server(cfg).run, daemon=True).start()
            clients[a] = (client or HttpService)(f"http://127.0.0.1:{base_port + i}")
        time.sleep(startup)
        return clients

    # ---- execution of the plan ------------------------------------------------------

    def run(self, store, services=None, log=print, trace=False, plan=None, phase3=agenda.execute):
        """Execute the plan on the record in `store`. Returns the instance of Z₀ that ran it.

        trace: after every invocation, show its bindings and intermediate values (model.explain).
        plan: a plan to use instead of the system's own (e.g. with a KPI step added).
        phase3: what executes a phase-3 step: the agenda of this process (the default), or the
                coordinator of workers that each run their own Z₀ (workers.py).
        """
        self.trace = trace
        services = dict(services or self.services(store))
        for a in self.all_abstractions():                # KPI abstractions run in process unless given
            services.setdefault(a, AbstractionService(store, a))
        z0 = Z0(store, services)
        if len(read(store)) > 1 and phase3 is not agenda.execute:
            raise ValueError("workers start on an empty record; an interrupted run is continued by the agenda "
                             "of one process (execution.mode: central)")
        if len(read(store)) > 1:                         # a record exists: walk it, then continue (resume.py)
            log(f"Resuming on a record of {len(read(store))} events: the schedule is walked again, nothing is rewritten")
            z0 = Walk(z0)
        self.abstractions = list(self.declared)          # a run adopts its new abstractions again
        self.agenda = list(self.abstractions)            # phase 3 starts with every abstraction
        self.sources = sources.make(self.declared_sources)   # every run starts from the declared seeds
        self.last = {}                                   # abstraction → last outcome (result, ω)
        self.outcomes = {a: {"I": 0, "A": 0, "U": 0, "H": 0, "F": 0} for a in self.abstractions}
        for step in (plan or self.plan):
            if "note" in step:
                log(f"-- {step['note']}")
            if step.get("phase") == 1:
                log("Phase 1  record criteria")
                for a in self.abstractions:
                    self._admit(z0, f"{a}/criterion.v1", log)
            elif step.get("phase") == 2:
                log("Phase 2  record ontologies")
                for a in self.abstractions:
                    self._admit(z0, f"{a}/ontology.v1", log)
            elif step.get("phase") == 3:
                log("Phase 3  execution (Axiom 0)")
                phase3(self, z0, step.get("max_admissions"), log)
            elif "govern" in step:
                log("Governed change: new specification versions (new regime)")
                for key in step["govern"]:
                    self._admit(z0, key, log)
                    a = key.split("/")[0]
                    if a in self.abstractions and a not in self.agenda:   # changed: evaluated again
                        self.agenda.append(a)
            elif step.get("kpi"):
                self.measure(z0, log)
            else:
                raise ValueError(f"unknown plan step {step}")
        return z0

    def adopt(self, name, z0=None):
        """An abstraction that a candidate has brought into being by carrying its specifications
        (substrate/governance.py) exists for the rest of the run: it is added to the abstractions,
        its outcomes are counted, and Z₀ is given a service for it in this process. One the system
        already has is left as it is. Returns True if it was new.
        """
        if name in self.abstractions:
            return False
        self.abstractions.append(name)
        self.outcomes[name] = {"I": 0, "A": 0, "U": 0, "H": 0, "F": 0}
        if z0 is not None and name not in z0.services:
            z0.services[name] = AbstractionService(z0.store, name)
        return True

    def measure(self, z0, log=print):
        """Compute the execution indicators now: admit a profile, then the system's KPI (kpi.py).

        The KPI abstractions are recorded (phases 1 and 2) the first time they are needed.
        Returns (profile result, kpi result or None); each is (result, ω).
        """
        log("KPI  execution indicators, on demand")
        if lookups.active(z0.prefix(), kpi.PROFILE, "criterion") is None:   # first profile: of the abstractions now
            self.specs.update(kpi.profile_specs(self.abstractions))
        for a in [kpi.PROFILE] + ([self.kpi] if self.kpi else []):
            for role in ("criterion", "ontology"):
                if lookups.active(z0.prefix(), a, role) is None:
                    self._admit(z0, f"{a}/{role}.v1", log)
        n = len(z0.prefix())
        profile = z0.execute(kpi.PROFILE, kpi.observation(self, z0.prefix()))
        log(f"   C^{n:<3} {kpi.PROFILE:12} → {profile[0]}")
        measured = None
        if self.kpi:
            n = len(z0.prefix())
            measured = z0.execute(self.kpi)
            log(f"   C^{n:<3} {self.kpi:12} → {measured[0]}" + (f"   ω = {_short(measured[1])}" if measured[1] else ""))
        C = z0.prefix()
        for source in (kpi.PROFILE, self.kpi):                 # agents that read the indicators
            for b in agenda.dependents(self, C, source) if source else ():
                if b not in self.agenda:
                    self.agenda.append(b)
        return profile, measured

    def _admit(self, z0, key, log):
        """Phases 1 and 2 (and governed changes): record one specification in C."""
        s = dict(self.specs[key])
        if s["role"] == "criterion":
            r = z0.admit_criterion(s)
        else:
            # phase 2 binds the ontology to the address of the criterion active in C (lineage, §3.1.2)
            s["criterion"] = lookups.active(z0.prefix(), s["abstraction"], "criterion")
            r = z0.admit_ontology(s)
        log(f"   {key:22} {r}")
        return r


def _short(v, limit=120):
    """A value as JSON, cut to `limit` characters for the log."""
    import json
    text = json.dumps(v, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit - 2] + " …"
