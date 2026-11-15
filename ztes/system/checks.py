"""The static check of a system: before anything is recorded, is it well formed?

The check uses the same rules as τ_root (model.validation for the API, substrate.governance for
versions and lineage), so a system that passes `check` has no specification that Z₀ would refuse.
"""
from ..model import validation
from ..model.epistemic import lineages
from ..substrate.governance import refusal
from ..substrate.lookups import active
from ..substrate.store import MemoryStore, read
from ..substrate.z0 import Z0
from . import sources


def check(system, log=print):
    """Check a system without executing it. Returns a list of problems (empty: the system is well formed).

    1. versions of every specification are numbered 1, 2, … without gaps;
    2. every plan step is known and every key named in a govern step exists;
    3. every specification is a well-formed API (model.validation), with the reason if it is not;
    4. every specification is admissible under τ_root in plan order: phases 1 and 2 and the
       governed changes are recorded in a scratch record in memory (phase 3 is not run);
    5. lineages read from outside the system are reported (their readers will wait);
    6. DESIGN.md is present.
    """
    problems = sources.problems(system.declared_sources, system.abstractions)
    for a in system.declared_sources:
        if a in system.abstractions and not system.specs[f"{a}/ontology.v1"].get("boundary"):
            problems.append(f"sources: {a} has a source but its ontology is not a boundary ontology")
    for a in system.abstractions + ([system.kpi] if system.kpi else []):
        for role in ("criterion", "ontology"):
            vs = sorted(int(k.rsplit(".v", 1)[1]) for k in system.specs if k.startswith(f"{a}/{role}.v"))
            if vs != list(range(1, len(vs) + 1)):
                problems.append(f"{a}/{role}: versions {vs} are not 1, 2, … without gaps")
    steps = []
    for step in system.plan:
        if step.get("phase") in (1, 2):
            steps += [f"{a}/{'criterion' if step['phase'] == 1 else 'ontology'}.v1" for a in system.abstractions]
        elif step.get("phase") == 3:
            pass
        elif step.get("kpi"):                                      # KPI abstractions, recorded when first needed
            for a in ["profile"] + ([system.kpi] if system.kpi else []):
                for role in ("criterion", "ontology"):
                    if f"{a}/{role}.v1" not in steps:
                        steps.append(f"{a}/{role}.v1")
        elif "govern" in step:
            for key in step["govern"]:
                if key in system.specs:
                    steps.append(key)
                else:
                    problems.append(f"plan: govern names {key}, which has no file")
        else:
            problems.append(f"plan: unknown step {step}")
    malformed = set()
    for key, s in system.specs.items():                       # 3: the API, independent of C
        # an ontology is bound to its criterion only when it is recorded (phase 2): not yet here
        unbound = dict(s, criterion="") if s["role"] == "ontology" and "criterion" not in s else s
        found = validation.problems(unbound)
        problems += [f"{key}: {m}" for m in found]
        if found:
            malformed.add(key)
    z0 = Z0(MemoryStore(), {})                                 # 4: τ_root in plan order, on a scratch record
    for key in steps:
        if key in malformed:
            continue
        s = dict(system.specs[key])
        if s["role"] == "ontology":
            s["criterion"] = active(read(z0.store), s["abstraction"], "criterion")
        why = refusal(read(z0.store), s)
        if why is not None:
            problems.append(f"{key}: refused by τ_root: {why}")
            continue
        (z0.admit_criterion if s["role"] == "criterion" else z0.admit_ontology)(s)   # recorded by Z₀
    external = sorted({b for s in system.specs.values() for b in lineages(s)} - set(system.all_abstractions()))
    if system.path is not None and not (system.path / "DESIGN.md").exists():
        problems.append("DESIGN.md is missing")
    log(f"Check  {system.name}: {len(system.abstractions)} abstractions, {len(system.specs)} specifications, "
        f"{len(system.plan)} plan steps")
    if external:
        log(f"   external lineages (readers will wait on them): {external}")
    for p in problems:
        log(f"   problem: {p}")
    log("   OK" if not problems else f"   {len(problems)} problem(s)")
    return problems

