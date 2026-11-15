"""[C] κ(C): what a specification reads from the record.       Paper: §9.1.1, §5.1, Definition 10, S1.4

A specification declares every input it uses; the model passes to the body nothing else,
so every datum that can influence a result is in the record (S1.4; the input bindings κω, κτ
of §9.1.1). The inputs are

    constants          named JSON values, part of the specification
    derived            named expressions over the constants and the library, computed once
                       per specification content (e.g. a distance matrix)
    inputs.context     named bindings over C, evaluated in order:
                         {"from": a | [a, …],                     lineages read: the horizon
                          "select": "last"|"first"|"one"|"all"|"count"|"exists"|"map",
                          "type": T,                               how payloads are read (types.py)
                          "where": "expr over x",                  optional filter; may use x, the
                                                                   constants and earlier bindings
                          "window": K,                             with "all": only the last K
                                                                   qualifying events (K an integer
                                                                   or the name of a constant)
                          "default": v}                            value while nothing qualifies
                       "select": "map" also has "key" (and optionally "value"), expressions
                       over x; it gives a read-only mapping {key: value}.

The union of "from" over both specifications of an abstraction is its event horizon
(Definition 10, §5.1): its result can change only when an event of one of these lineages is
admitted, or when its own specification changes. The agenda of Z₀ relies on exactly this.
A window narrows what is read inside a lineage, not the horizon: older events remain in C and
are simply not read, so forgetting needs no change of the record (S1.1).

Performance. Bindings are answered from the index of the record (view.py), never by scanning
C; a map is kept in that index and extended with each new event, so no invocation rebuilds it;
the derived values and the namespace of a specification are prepared once and reused.
"""
from collections.abc import Mapping
from types import MappingProxyType

from . import types
from .errors import Undefined
from .language import expression, namespace
from .view import indexed

SELECT = ("last", "first", "one", "all", "count", "exists", "map")


def lineages(s):
    """[C] The lineages a specification reads: the union of its "from" fields (its part of the horizon)."""
    out = []
    for b in s["inputs"]["context"].values():
        for a in ([b["from"]] if isinstance(b["from"], str) else b["from"]):
            if a not in out:
                out.append(a)
    return out


def freeze(v):
    """An immutable copy: lists become tuples, dicts read-only mappings. Shared values cannot be altered."""
    if isinstance(v, (list, tuple)):
        return tuple(freeze(x) for x in v)
    if isinstance(v, dict):
        return MappingProxyType({k: freeze(x) for k, x in v.items()})
    return v


# ---- what is prepared once per specification: namespace, constants, derived values ----

class Prepared:
    """The parts of a specification that do not depend on C, computed once.

        ns     the functions its body may call (language.namespace)
        base   its constants and derived values (derived values frozen)
        maps   for each map binding, the key under which its entries are kept in the index
    """
    __slots__ = ("spec", "ns", "base", "maps")

    def __init__(self, s):
        self.spec = s                                          # kept alive: id(s) cannot be reused
        self.ns = namespace(s.get("library", ""))
        tag = types.canon([s.get("constants", {}), s.get("derived", {}), s.get("library", "")])
        self.base = {**s.get("constants", {}), **derived(s, self.ns, tag)}
        self.maps = {name: map_key(tag, b) for name, b in s["inputs"]["context"].items() if b["select"] == "map"}


_PREPARED = {}
_DERIVED = {}


def prepared(s):
    """The Prepared form of s, cached by identity (specifications loaded from C are shared objects)."""
    p = _PREPARED.get(id(s))
    if p is None or p.spec is not s:
        p = _PREPARED[id(s)] = Prepared(s)
    return p


def derived(s, ns, tag=None):
    """The derived values of a specification, computed once per content of constants, derived and library."""
    if not s.get("derived"):
        return {}
    tag = tag or types.canon([s.get("constants", {}), s["derived"], s.get("library", "")])
    if tag not in _DERIVED:
        env = dict(s.get("constants", {}))
        for name, expr in s["derived"].items():
            env[name] = expression(expr, env, ns)
        _DERIVED[tag] = {k: freeze(env[k]) for k in s["derived"]}
    return dict(_DERIVED[tag])                                 # immutable values: shared, never copied


# ---- "select": "map": a mapping over the horizon, kept in the index ----

def map_key(tag, b):
    """The key of a map in the index: the same content of specification and binding, the same map."""
    src = [b["from"]] if isinstance(b["from"], str) else b["from"]
    return types.canon([tag, src, b.get("type", "json"), b.get("key"), b.get("value"), b.get("where")])


def _key(k):
    """A map key as a hashable value: lists (JSON arrays) become tuples."""
    return tuple(_key(v) for v in k) if isinstance(k, list) else k


class RecordMap(Mapping):
    """[C] A read-only view {key: value} of a map binding over the prefix of length n.

    The entries are shared with the index of the record (key → (position, value)); the view
    shows only those recorded before position n, so no prefix needs its own copy. Values are
    frozen when they enter the map, so a body cannot alter them.
    """
    __slots__ = ("_entries", "_n")

    def __init__(self, entries, n):
        self._entries, self._n = entries, n

    def __getitem__(self, k):
        if k.__class__ is list:
            k = _key(k)
        hit = self._entries.get(k)
        if hit is None or hit[0] >= self._n:
            raise KeyError(k)
        return hit[1]

    def __contains__(self, k):
        if k.__class__ is list:
            k = _key(k)
        hit = self._entries.get(k)
        return hit is not None and hit[0] < self._n

    def get(self, k, default=None):
        return self[k] if k in self else default

    def __iter__(self):
        return (k for k, (pos, _) in self._entries.items() if pos < self._n)

    def __len__(self):
        return sum(1 for pos, _ in self._entries.values() if pos < self._n)


def _map(ix, n, name, b, src, t, env, ns, tag):
    """The entries of a map binding over Cⁿ, extended in the index with the events not yet in it."""
    cache = ix.maps.get(tag)
    if cache is None:
        cache = ix.maps[tag] = {"upto": 0, "entries": {}}
    if n > cache["upto"]:
        entries = cache["entries"]
        for pos, p in ix.items_between(src, cache["upto"], n):
            x = types.decode(t, p)
            if "where" in b and not expression(b["where"], {**env, "x": x}, ns):
                continue
            k = _key(expression(b["key"], {**env, "x": x}, ns))
            if k in entries:
                raise ValueError(f"binding '{name}': key {k!r} occurs twice")
            entries[k] = (pos, freeze(expression(b["value"], {**env, "x": x}, ns) if "value" in b else x))
        cache["upto"] = n
    return RecordMap(cache["entries"], n)                     # a view of the prefix: no copy


# ---- one binding, and the whole context ----

def bind(C, name, b, env=None, ns=None, key=None):
    """[C] Evaluate one declared binding over the prefix C; env holds the constants and earlier bindings.

    key: for a map, the key of its entries in the index (Prepared.maps).
    """
    src = [b["from"]] if isinstance(b["from"], str) else b["from"]
    t = b.get("type", "json")
    sel = b["select"]
    ix, n = indexed(C), len(C)
    env = env or {}
    if sel == "map":
        return _map(ix, n, name, b, src, t, env, ns, key or map_key(None, b))
    if "where" not in b and sel in ("count", "exists"):        # no value is needed: count positions
        k = ix.count(src, n)
        return k if sel == "count" else k > 0
    if "where" not in b and sel == "last":                     # only the latest value is decoded
        p = ix.last(src, n)
        if p is not None:
            return types.decode(t, p)
        if "default" in b:
            return types.decode(t, b["default"])
        raise Undefined(f"{name}: no event in {src} yet")
    raw = ix.payloads(src, n)                                  # payloads of the horizon, in record order
    k = b.get("window")                                        # the last K qualifying events only
    if k is not None:
        k = env[k] if isinstance(k, str) else k
        if "where" not in b:
            raw = raw[-k:]                                     # decode only what is read
    if "where" in b:
        xs = [x for x in (types.decode(t, p) for p in raw) if expression(b["where"], {**env, "x": x}, ns)]
        if k is not None:
            xs = xs[-k:]
    elif sel == "first":
        xs = [types.decode(t, raw[0])] if raw else []
    else:
        xs = [types.decode(t, p) for p in raw]
    if sel == "one" and len(xs) > 1:
        raise ValueError(f"binding '{name}': select one found {len(xs)} events")
    if sel == "all":
        return xs
    if sel == "count":
        return len(xs)
    if sel == "exists":
        return bool(xs)
    if xs:
        return xs[-1] if sel == "last" else xs[0]              # last, or first / one
    if "default" in b:
        return types.decode(t, b["default"])
    raise Undefined(f"{name}: no event in {src} yet")


def missing(C, s):
    """[C] What the horizon of s still lacks in Cⁿ, in words; None when the horizon is complete.

    This is decided by the existence of events alone, by counting in the index: no payload is
    decoded and nothing is computed. Two declarations say which events must exist:

      "requires": {"dp": "NEEDED", "tour": 1}   at least that many events of each lineage
                                                (a number, or the name of a constant);
      a binding that selects one event (last, first, one) of a lineage, without a filter and
      without a default.

    The other way to ⊥ is through the body: every required event exists, and the body,
    computed on their content, yields no candidate. Both are Not Yet for Z₀; only this one is free.
    """
    ix, n = indexed(C), len(C)
    for lineage, k in s.get("requires", {}).items():
        k = s["constants"][k] if isinstance(k, str) else k
        have = ix.count([lineage], n)
        if have < k:
            return f"requires {k} event(s) of {lineage}, C^{n} has {have}"
    for name, b in s["inputs"]["context"].items():
        if b["select"] in ("last", "first", "one") and "where" not in b and "default" not in b:
            src = [b["from"]] if isinstance(b["from"], str) else b["from"]
            if ix.count(src, n) == 0:
                return f"{name}: no event in {src} yet"
    return None


def project(C, s):
    """[C] κ(C): the constants, the derived values, and every declared binding of s on the prefix C, in order.

    Raises Undefined (⊥) when the horizon is incomplete (missing), before anything is read, or
    when a filtered binding finds no qualifying event and has no default.
    """
    if (m := missing(C, s)) is not None:
        raise Undefined(m)
    p = prepared(s)
    env = dict(p.base)
    for name, b in s["inputs"]["context"].items():
        env[name] = bind(C, name, b, env, p.ns, p.maps.get(name))
    return env
