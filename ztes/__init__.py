"""ztes: a minimal Zero Tier Execution Substrate for the OEE execution calculus.

One possible implementation of the ZTES execution model [50], which is independent of
infrastructure and design method; here it serves to demonstrate the calculus of
"A Calculus of Execution for Systems of Interacting Binary Relations: Contextual Resolution,
Separated Admission, and an Inseparable Execution Substrate". Section, theorem and table
numbers in the comments refer to that paper.

The package keeps the model apart from the substrate that executes it:

    model/       the OEE model: what a specification is and how it is evaluated
                   epistemic.py [C], ontological.py [ω], eschatological.py [τ],
                   view, language, types, validation, explain, errors
    substrate/   Z₀, the zero-tier execution substrate, and the record C it writes
                   store, events, lookups, governance (τ_root), z0 (Axiom 0), replay (R2)
    service.py   an abstraction as a microservice: Z₀ asks it for steps 3a and 3b
    system/      a system given as a directory of files: authoring, plan, agenda, checks, reports
    __main__.py  command line: python -m ztes new | check | design | run | verify | explain | serve

Dependencies go one way: system → substrate → model. The model does not import the
substrate; the substrate contains no domain content. Systems live in examples/.

Tags used in docstrings and comments, so that each part names what it implements:

    [C]      epistemic axis: the record, what is read from it (κ(C)), how it is written
    [ω]      ontological axis: Sω, realization, ⊥ (Not Yet)                        D1
    [τ]      eschatological axis: Sτ, judgment, exactly one Boolean                 D2
    [Z₀]     the zero-tier execution substrate: Axiom 0, τ_root, the only writer to C
    [A0]     one application of Axiom 0 (an invocation: steps 3a, 3b, 3c)
    [S1.k]   the substrate conditions S1.1–S1.5 (§3.4.1)
    [R1]     governance internal to execution; [R2] replay from the record alone
"""
