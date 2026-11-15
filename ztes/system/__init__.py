"""Running a system: a directory of specifications, its plan, and its reports.

This layer is tooling around the calculus. It prepares specifications for Z₀ (step 0 and the
authoring form), drives phase 3 (the agenda) and reports on C. What is admitted, and why, is
decided only by the model (ztes.model) and by Z₀ (ztes.substrate).

    authoring.py  the short authoring form, expanded into complete recorded specifications
    system.py     System: load a system, run its plan, start its services
    agenda.py     phase 3: the agenda, termination, and the final state of each abstraction
    checks.py     the static check of a system, before anything is recorded
    report.py     the record as text, explain an event, compare with "expect", R2 report
    scaffold.py   the skeleton of a new system (python -m ztes new)
"""
