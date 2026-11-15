"""[C] Value types: how a JSON payload is read for computation and written back.   Paper: §3.2.5, §9.1

A payload in C is a JSON value. A type is a codec between that JSON value and the
value an expression computes with. Types are written in specifications:

    basic       "integer" | "rational" | "boolean" | "text" | "json"
    composite   {"list": T}            a JSON array of T
                {"record": {f: T, …}}  a JSON object with exactly these fields

A new basic type is one entry in BASIC; nothing else in the model or in Z₀ changes.
encode is strict: a value of the wrong type is a contract violation of the
specification, not something to be repaired silently.
"""
import json
from collections.abc import Mapping
from fractions import Fraction


def canon(x):
    """Canonical JSON: the same content always gives the same text (used for addresses and cache keys)."""
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _no_float(x, t):
    if isinstance(x, float):
        raise TypeError(f"{x!r} is a float, not {t}: use Fraction(a, b) or // instead of a / b")


def _integer(x):
    _no_float(x, "an integer")
    if isinstance(x, Fraction) and x.denominator == 1:
        x = int(x)
    if isinstance(x, bool) or not isinstance(x, int):
        raise TypeError(f"not an integer: {x!r}")
    return x


def _rational(x):
    _no_float(x, "a rational")
    if isinstance(x, bool) or not isinstance(x, (int, Fraction)):
        raise TypeError(f"not a rational: {x!r}")
    return Fraction(x)


def _of(t):
    def check(x):
        if not isinstance(x, t):
            raise TypeError(f"not a {t.__name__}: {x!r}")
        return x
    return check


#            name        decode (JSON → value)          encode (value → JSON)
BASIC = {
    "integer":  (lambda v: _integer(v),            lambda x: _integer(x)),
    "rational": (lambda v: Fraction(v),            lambda x: str(_rational(x))),
    "boolean":  (_of(bool),                        _of(bool)),
    "text":     (_of(str),                         _of(str)),
    "json":     (lambda v: v,                      lambda x: x),
}


def valid(t):
    """Is t a well-formed type?"""
    if isinstance(t, str):
        return t in BASIC
    if isinstance(t, dict) and len(t) == 1:
        (k, v), = t.items()
        if k == "list":
            return valid(v)
        if k == "record":
            return isinstance(v, dict) and all(valid(x) for x in v.values())
    return False


def decode(t, v):
    """JSON payload → value. Called for every payload a binding reads, so the common cases come first."""
    if t.__class__ is str:
        if t == "json" or (t == "integer" and v.__class__ is int):
            return v
        return BASIC[t][0](v)
    if "list" in t:
        u = t["list"]
        return [decode(u, x) for x in v]
    u = t["record"]
    if not isinstance(v, dict) or v.keys() != u.keys():
        raise TypeError(f"record fields {sorted(v)} differ from {sorted(u)}")
    return {f: decode(u[f], v[f]) for f in u}


def encode(t, x):
    if isinstance(t, str):
        return BASIC[t][1](x)
    (k, u), = t.items()
    if k == "list":
        if not isinstance(x, (list, tuple)):
            raise TypeError(f"not a list: {x!r}")
        return [encode(u, y) for y in x]
    if not isinstance(x, Mapping) or set(x) != set(u):
        raise TypeError(f"not a record with fields {sorted(u)}: {x!r}")
    return {f: encode(u[f], x[f]) for f in u}
