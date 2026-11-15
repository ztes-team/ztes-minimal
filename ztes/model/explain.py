"""[C][ω][τ] One evaluation shown step by step: inputs, derived values, intermediate results.

Used by `run --trace` and `explain`. It performs the same evaluation as realize (ontological.py)
and judge (eschatological.py), on the same prefix, so it shows exactly what produced a
recorded event: the constants and derived values, each binding κ(C), the candidate, and ω or τ.
"""
from fractions import Fraction

from . import language, types
from .epistemic import RecordMap, bind, missing, prepared
from .errors import Undefined, where_of


def _show(v):
    if isinstance(v, RecordMap):
        return f"map of {len(v)} entries"
    if isinstance(v, Fraction):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_show(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {_show(x)}" for k, x in v.items()) + "}"
    return repr(v)


def _brief(v, limit=160):
    """A value as text, shortened when it is long (e.g. a derived table)."""
    text = _show(v)
    if len(text) <= limit:
        return text
    size = f"{len(v)} items: " if hasattr(v, "__len__") else ""
    return f"{size}{text[:limit - 20]} …"


def explain(C, s, w=None):
    """Re-evaluate one specification on C step by step. Returns lines of text.

    For an ontology (w is None) the lines end with ω or ⊥; for a criterion, with the judgment
    of the candidate w.
    """
    p = prepared(s)
    lines = [where_of(s)]
    env = dict(s.get("constants", {}))
    for name, value in env.items():
        lines.append(f"  constant {name} = {_brief(value)}")
    for name in s.get("derived", {}):
        env[name] = p.base[name]
        lines.append(f"  derived  {name} = {_brief(env[name])}")
    if s.get("library"):
        lines.append(f"  library  {', '.join(language.library_names(s['library']))}")
    if (m := missing(C, s)) is not None:                                 # [C] the horizon is incomplete
        lines.append(f"  {m} → ⊥, Not Yet (nothing computed)")
        return lines
    for name, b in s["inputs"]["context"].items():                       # [C] κ(C)
        try:
            env[name] = bind(C, name, b, env, p.ns, p.maps.get(name))
            lines.append(f"  binding  {name} = {_brief(env[name])}")
        except Undefined as x:
            lines.append(f"  binding  {name}: no qualifying event ({x}) → ⊥, Not Yet")
            return lines
    if w is not None:
        candidate = s["inputs"]["candidate"]
        env[candidate["name"]] = types.decode(candidate["type"], w)
        lines.append(f"  candidate {candidate['name']} = {_show(env[candidate['name']])}")
    body = s["body"]
    if language.is_function(body):
        r = language.call(body, env, p.ns)
        lines.append(f"  function → {_show(r)}")
    else:
        for name, expr in body.items():
            env[name] = language.expression(expr, env, p.ns)
            if name != "result":
                lines.append(f"  {name} = {_brief(env[name])}")
        r = env["result"]
    if w is None:
        lines.append("  ω = " + ("⊥ (None): Not Yet" if r is None else _show(r)))   # [ω]
    else:
        lines.append(f"  τ = {r}")                                                    # [τ]
    return lines
