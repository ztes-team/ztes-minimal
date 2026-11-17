"""[C] Value types: how a JSON payload is read for computation and written back.   Paper: §3.2.5, §9.1

A payload in C is a JSON value. A type is a codec between that JSON value and the
value an expression computes with. Types are written in specifications:

    basic       "integer" | "rational" | "boolean" | "text" | "json" | "specification"
    composite   {"list": T}            a JSON array of T
                {"record": {f: T, …}}  a JSON object with exactly these fields

"specification" is a JSON object read as it is; that it is a well-formed specification is not a
question of its type but of τ_root, which judges it when a candidate carries it (carried_field).

A new basic type is one entry in BASIC; nothing else in the model or in Z₀ changes.
A payload is read by the decoder of its type, compiled once per type (decoder, _compile).
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
    """Refuse a float: a value in C is exact (an integer, or a rational written "p/q")."""
    if isinstance(x, float):
        raise TypeError(f"{x!r} is a float, not {t}: use Fraction(a, b) or // instead of a / b")


def _integer(x):
    """An integer: an int, or a Fraction whose denominator is 1 (made an int); not a bool, not a float."""
    _no_float(x, "an integer")
    if isinstance(x, Fraction) and x.denominator == 1:
        x = int(x)
    if isinstance(x, bool) or not isinstance(x, int):
        raise TypeError(f"not an integer: {x!r}")
    return x


def _rational(x):
    """A rational (Fraction) from an int or a Fraction; not a bool, not a float."""
    _no_float(x, "a rational")
    if isinstance(x, bool) or not isinstance(x, (int, Fraction)):
        raise TypeError(f"not a rational: {x!r}")
    return Fraction(x)


def _of(t):
    """A codec for a basic type that is one Python type t: it lets values of t pass and refuses others."""
    def check(x):
        """x itself, if it is of type t; TypeError otherwise."""
        if not isinstance(x, t):
            raise TypeError(f"not a {t.__name__}: {x!r}")
        return x
    return check


def _plain(x):
    """A value as plain JSON: read-only mappings become dicts and tuples lists, all the way down."""
    if isinstance(x, Mapping):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _specification(x):
    """A specification as a payload: a JSON object, written as plain JSON (a frozen value is thawed)."""
    if not isinstance(x, Mapping):
        raise TypeError(f"not a specification (a JSON object): {x!r}")
    return _plain(x)


#            name        decode (JSON → value)          encode (value → JSON)
BASIC = {
    "integer":  (lambda v: _integer(v),            lambda x: _integer(x)),
    "rational": (lambda v: Fraction(v),            lambda x: str(_rational(x))),
    "boolean":  (_of(bool),                        _of(bool)),
    "text":     (_of(str),                         _of(str)),
    "json":     (lambda v: v,                      lambda x: x),
    "specification": (_specification,                _specification),
}

CARRIED = {"list": "specification"}           # the type of the field in which a candidate carries specifications


def carried_field(t):
    """The field of a record type t in which a candidate carries specifications: the one field whose
    type is {"list": "specification"}; None if t is not a record or has no such field. (Validation
    refuses an ontology that declares more than one.)
    """
    if not isinstance(t, dict) or "record" not in t:
        return None
    fields = [f for f, u in t["record"].items() if u == CARRIED]
    return fields[0] if len(fields) == 1 else None


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
    """JSON payload → value. Called for every payload a binding reads, so each type is compiled once
    into a decoder (decoder below); it gives the same values and raises the same errors as the
    recursive reading of t, with a fast path for a list of plain integers.
    """
    return decoder(t)(v)


_DECODERS = {}                  # id(t) → (t, its decoder); t is kept, so its id is not reused


def decoder(t):
    """The decoder of type t, compiled on first use."""
    hit = _DECODERS.get(id(t))
    if hit is None or hit[0] is not t:
        hit = _DECODERS[id(t)] = (t, _compile(t))
    return hit[1]


def _compile(t):
    """The decoder of type t, built from the decoders of its parts. It reads as the recursive
    definition does: a basic type by BASIC ("json" as it is, a plain int without a call), a list
    element by element, a record with exactly its fields, each by its decoder, in the order of t.
    """
    if t.__class__ is str:
        if t == "json":
            return _as_is
        if t == "integer":
            return _integer_value
        return BASIC[t][0]
    if "list" in t:
        u = t["list"]
        if u == "integer":
            return _integers
        item = decoder(u)
        return lambda v: [item(x) for x in v]
    u = t["record"]
    fields = [(f, decoder(u[f])) for f in u]
    keys = u.keys()

    def record(v):
        """A record: exactly the declared fields, each read by its decoder; TypeError otherwise."""
        if not isinstance(v, dict) or v.keys() != keys:
            raise TypeError(f"record fields {sorted(v)} differ from {sorted(u)}")
        return {f: d(v[f]) for f, d in fields}
    return record


def _as_is(v):
    """A "json" value is read as it is."""
    return v


def _integer_value(v):
    """An integer by the rule of _integer, without a call when v is a plain int."""
    return v if v.__class__ is int else _integer(v)


_INT = {int}


def _integers(v):
    """A list of integers: when every element is a plain int, one copy of the list."""
    if set(map(type, v)) <= _INT:
        return list(v)
    return [_integer_value(x) for x in v]


def encode(t, x):
    """Value → JSON payload, strictly: a value of the wrong type is a TypeError, never repaired."""
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
