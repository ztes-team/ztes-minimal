"""The OEE model: what a specification is and how it is evaluated.     Paper: §3, §3.4.4, §9.1.1

The three axes of the lifting each have their own module:

    epistemic.py       [C]  κ(C): what a specification reads from the record (bindings, maps,
                            constants, derived values); its horizon             §9.1.1, Def. 10
    ontological.py     [ω]  Sω: realization, ω or ⊥ (Not Yet)                   §3.4.1, D1
    eschatological.py  [τ]  Sτ: judgment, exactly one Boolean                   §3.4.1, D2

and around them

    view.py            [C]  the record as the model reads it: a prefix Cⁿ and its index
    language.py             the language of bodies: expressions, functions, libraries (S1.2)
    types.py           [C]  payload types: codecs between JSON and computed values
    validation.py           well-formedness of a specification as an API (used by τ_root)
    explain.py              the same evaluation, step by step (trace, explain)
    errors.py               ⊥ (Undefined) and defects of specifications (SpecError)

The model never writes C, never sees a store, and does not import ztes.substrate. It is the
part that Axiom 0 evaluates; Z₀, which applies Axiom 0 and records the results, is in
ztes.substrate.
"""
from .eschatological import judge
from .errors import SpecError, Undefined
from .epistemic import missing
from .ontological import realize
from .validation import problems
