"""[Sω/Sτ] Well-formedness of a specification as an API, independent of C.   Paper: §3.4.4, §9.1.1, S1.2

A specification is data: phases 1 and 2 record it, phase 3 evaluates it. problems(s) says
whether it is a well-formed API before it is recorded, so that a malformed specification is
refused by τ_root (substrate/governance.py) and found by `check`, never at execution:

    identity     role "criterion" | "ontology", an abstraction name, a version ≥ 1
    constants    a JSON object
    library      obeys the rules of language.py; a def calls only defs written before it
    derived      each expression uses only constants, the library and earlier derived values
    bindings     a known select, a valid type, a "where" that uses only x, the constants and
                 earlier bindings, a default that decodes under its type; a map has a key, and
                 its key, value and where use no other binding (it is kept in the index); a
                 window belongs to select "all" and is a positive integer or names one
    body         expressions: each compiles, uses only declared names, and "result" is defined;
                 a function: obeys language.py, and its parameters are declared inputs
    criterion    [τ] returns "boolean", total, a typed candidate, and a value for every
                 binding that might be missing (defaults for last, first, one): Sτ is total
    ontology     [ω] partial, a valid return type, and a field "criterion" naming the criterion
                 it is bound to (which criterion is a question about C: τ_root checks it);
                 a boundary ontology ("boundary": true, §5.2) has no body: its candidate is the
                 occurrence bound to the invocation

What the specification means for its domain is not checked here: that is the role of its
criterion in phase 3.
"""
from . import language, types
from .epistemic import SELECT


def problems(s):
    """The rule violations of a specification, as located messages (empty: well formed)."""
    try:
        return _problems(s)
    except (KeyError, TypeError, ValueError, AttributeError, SyntaxError) as x:
        return [f"malformed specification: {type(x).__name__}: {x}"]


def _compiles(expr, what):
    try:
        compile(expr, f"<{what}>", "eval")
        return []
    except SyntaxError as x:
        return [f"{what}: {x.msg}"]


def _problems(s):
    out = []
    role, a, v = s["role"], s["abstraction"], s["version"]
    if role not in ("criterion", "ontology"):
        return [f"role {role!r} is neither criterion nor ontology"]
    if not isinstance(a, str) or not a:
        out.append("abstraction must be a name")
    if not isinstance(v, int) or isinstance(v, bool) or v < 1:
        out.append("version must be an integer ≥ 1")
    constants = s.get("constants", {})
    if not isinstance(constants, dict):
        return out + ["constants must be a JSON object"]

    # ---- library and derived values: names available to every expression ----
    lib = s.get("library", "")
    if lib:
        out += [f"library: {p}" for p in language.library_problems(lib, language.SAFE)]
        if out:
            return out
    functions = set(language.SAFE) | set(language.library_names(lib))
    static = functions | language.CONSTANT_NAMES | set(constants)
    for name, expr in s.get("derived", {}).items():
        bad = _compiles(expr, f"derived '{name}'")
        out += bad
        if not bad and language.free_names(expr) - static:
            out.append(f"derived '{name}' uses undeclared {sorted(language.free_names(expr) - static)}")
        static.add(name)

    # ---- [C] bindings ----
    context = s["inputs"]["context"]
    earlier = set()
    for name, b in context.items():
        out += [f"binding '{name}': {p}" for p in _binding_problems(b, role == "criterion", static, earlier, constants)]
        earlier.add(name)

    # ---- [C] the events that must exist before the body is evaluated ----
    if "requires" in s:
        from .epistemic import lineages
        requires = s["requires"]
        if role != "ontology" or s.get("boundary") is True:
            out.append("requires belongs to an ontology with a body: a criterion is total, a boundary candidate is not computed")
        elif not isinstance(requires, dict):
            out.append('requires must be a JSON object {"lineage": count}')
        else:
            for lineage, k in requires.items():
                if lineage not in lineages(s):
                    out.append(f"requires names {lineage!r}, which no binding reads: it is outside the horizon")
                k = constants.get(k) if isinstance(k, str) else k
                if not isinstance(k, int) or isinstance(k, bool) or k < 1:
                    out.append(f"requires {lineage!r}: the count is not a positive integer or the name of one among the constants")

    # ---- the body ----
    known = static | set(context)
    if role == "criterion":
        candidate = s["inputs"].get("candidate")
        if not isinstance(candidate, dict) or not isinstance(candidate.get("name"), str):
            out.append("a criterion needs a candidate {\"name\": …, \"type\": …}")
        else:
            if not types.valid(candidate.get("type")):
                out.append(f"candidate type {candidate.get('type')!r} is not a type")
            known.add(candidate["name"])
    if role == "ontology" and s.get("boundary") is True:
        if "body" in s:
            out.append("a boundary ontology has no body: its candidate is the occurrence of the invocation")
        body = None
    else:
        body = s["body"]
    if body is None:
        pass
    elif language.is_function(body):
        fn = language.problems(body, functions)
        out += [f"body function: {p}" for p in fn]
        if not fn:
            missing = set(language.parameters(body)) - known
            if missing:
                out.append(f"body function: parameters {sorted(missing)} are not declared inputs")
    elif not isinstance(body, dict) or "result" not in body:
        out.append('body: an object of expressions must define "result"')
    else:
        for name, expr in body.items():
            bad = _compiles(expr, f"body '{name}'")
            out += bad
            if not bad and language.free_names(expr) - known:
                out.append(f"body '{name}' uses undeclared {sorted(language.free_names(expr) - known)}")
            known.add(name)

    # ---- [τ] the contract of a criterion, [ω] the contract of an ontology ----
    if role == "criterion":
        if s.get("returns") != "boolean" or s.get("total") is not True:
            out.append('a criterion returns "boolean" and is total')
    else:
        if s.get("partial") is not True:
            out.append("an ontology is partial")
        if not types.valid(s.get("returns")):
            out.append(f"return type {s.get('returns')!r} is not a type")
        if "criterion" not in s:
            out.append("an ontology names the criterion it is bound to (phase 2 follows phase 1)")
    return out


def _binding_problems(b, criterion, static, earlier, constants=None):
    out = []
    src = b.get("from")
    if not (isinstance(src, str) or (isinstance(src, list) and src and all(isinstance(x, str) for x in src))):
        out.append('"from" must name a lineage or a nonempty list of lineages')
    sel = b.get("select")
    if sel not in SELECT:
        return out + [f"select {sel!r} is not one of {', '.join(SELECT)}"]
    t = b.get("type", "json")
    if not types.valid(t):
        return out + [f"type {t!r} is not a type"]
    if sel == "map":
        # a map is extended incrementally in the index, so its expressions may use only x,
        # the constants, the derived values and the library, never another binding
        if "key" not in b:
            out.append("a map needs a key")
        for f in ("key", "value", "where"):
            if f in b:
                bad = _compiles(b[f], f)
                out += bad
                if not bad and language.free_names(b[f]) - static - {"x"}:
                    extra = sorted(language.free_names(b[f]) - static - {"x"})
                    out.append(f"{f} uses {extra}: a map may use only x, constants, derived values and the library")
    elif "where" in b:
        bad = _compiles(b["where"], "where")
        out += bad
        if not bad and language.free_names(b["where"]) - static - earlier - {"x"}:
            out.append(f"where uses undeclared {sorted(language.free_names(b['where']) - static - earlier - {'x'})}")
    if "window" in b:
        k = b["window"]
        k = (constants or {}).get(k) if isinstance(k, str) else k
        if sel != "all":
            out.append('a window belongs to select "all"')
        elif not isinstance(k, int) or isinstance(k, bool) or k < 1:
            out.append(f"window {b['window']!r} is not a positive integer or the name of one among the constants")
    if "default" in b:
        try:
            types.decode(t, b["default"])
        except (TypeError, ValueError, KeyError, AttributeError) as x:
            out.append(f"default does not decode as {t}: {x}")
    if criterion and sel in ("last", "first", "one") and "default" not in b:
        out.append("a criterion binding with select last, first or one needs a default (τ is total)")
    return out
