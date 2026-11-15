"""[ω] ⊥ and [Sω/Sτ] defects of specifications.                       Paper: §3.4.1, §3.2.4

Two different things can stop an evaluation, and the model keeps them apart:

    Undefined   ⊥: the realization Sω is undefined on this prefix (partiality, not a value).
                Z₀ reads it as Not Yet: nothing is appended, the abstraction waits.
    SpecError   a defect of a specification (a failing expression, a broken contract).
                It is reported with its location and stops the run; it is never read as ⊥.
"""


class Undefined(Exception):
    """[ω] ⊥: a binding has no qualifying event and no default, so Sω is undefined here."""


class SpecError(Exception):
    """A specification failed while being evaluated: a defect of that specification, with its location."""


def where_of(s):
    """The location of a specification in messages: abstraction/role.v<version>."""
    return f"{s['abstraction']}/{s['role']}.v{s['version']}"
