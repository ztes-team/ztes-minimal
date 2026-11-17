"""Every type is compiled once into a decoder (types.decoder). The decoders must give what the
recursive decode gave before them, value for value and error for error: the old decode is written
here again and compared with the new one on random types and values, valid and invalid.
"""
import random
from fractions import Fraction

import pytest

from ztes.model import types
from ztes.model.types import BASIC, _integer


def old_decode(t, v):
    """types.decode as it was at 822d15c."""
    if t.__class__ is str:
        if t == "json" or (t == "integer" and v.__class__ is int):
            return v
        return BASIC[t][0](v)
    if "list" in t:
        u = t["list"]
        return [old_decode(u, x) for x in v]
    u = t["record"]
    if not isinstance(v, dict) or v.keys() != u.keys():
        raise TypeError(f"record fields {sorted(v)} differ from {sorted(u)}")
    return {f: old_decode(u[f], v[f]) for f in u}


def outcome(f, t, v):
    try:
        r = f(t, v)
        return ("value", r, _shape(r))
    except Exception as x:
        return ("error", type(x).__name__, str(x))


def _shape(r):
    """The Python types of a value, all the way down (1 and True and 1.0 compare equal)."""
    if isinstance(r, list):
        return ["list", [_shape(x) for x in r]]
    if isinstance(r, dict):
        return ["dict", list(r), [_shape(x) for x in r.values()]]
    return type(r).__name__


def random_type(rnd, depth=0):
    if depth > 2 or rnd.random() < 0.4:
        return rnd.choice(["integer", "rational", "boolean", "text", "json"])
    if rnd.random() < 0.5:
        return {"list": random_type(rnd, depth + 1)}
    return {"record": {f: random_type(rnd, depth + 1) for f in rnd.sample("abcd", rnd.randint(1, 3))}}


ODD = [1.5, 2.0, True, False, None, "7", "1/3", Fraction(4, 2), Fraction(1, 3), [], {}, -3, 0, 10 ** 30]


def random_value(rnd, t, noise):
    """A value of type t, or, with probability noise at every level, something else."""
    if rnd.random() < noise:
        return rnd.choice(ODD + [[1, 2], {"a": 1}])
    if t == "integer":
        return rnd.randint(-10 ** 6, 10 ** 6)
    if t == "rational":
        return rnd.choice([rnd.randint(-9, 9), f"{rnd.randint(-9, 9)}/{rnd.randint(1, 9)}"])
    if t == "boolean":
        return rnd.random() < 0.5
    if t == "text":
        return rnd.choice(["", "a", "Not Yet", "ω"])
    if t == "json":
        return rnd.choice(ODD + [[1, [2]], {"k": [1]}])
    if "list" in t:
        return [random_value(rnd, t["list"], noise) for _ in range(rnd.randint(0, 5))]
    fields = dict(t["record"])
    if rnd.random() < noise:                                   # a field missing or one too many
        if fields and rnd.random() < 0.5:
            fields.pop(next(iter(fields)))
        else:
            fields["z"] = "integer"
    return {f: random_value(rnd, u, noise) for f, u in fields.items()}


@pytest.mark.parametrize("seed", range(20))
def test_the_compiled_decoder_gives_what_the_old_decode_gave(seed):
    rnd = random.Random(seed)
    for _ in range(300):
        t = random_type(rnd)
        for noise in (0.0, 0.05, 0.3):
            v = random_value(rnd, t, noise)
            assert outcome(types.decode, t, v) == outcome(old_decode, t, v), (t, v)


@pytest.mark.parametrize("v", [[], [0, -1, 2 ** 70], [1, True], [1, 2.0], [1, Fraction(6, 3)], [1, Fraction(1, 2)],
                               [1, "2"], [None], (1, 2), "12", 5])
def test_lists_of_integers_on_the_fast_path_and_off_it(v):
    t = {"list": "integer"}
    assert outcome(types.decode, t, v) == outcome(old_decode, t, v)


def test_a_decoder_is_compiled_once_per_type_object_and_returns_new_values():
    t = {"record": {"walk": {"list": "integer"}, "length": "integer"}}
    v = {"walk": [0, 2, 1], "length": 7}
    assert types.decoder(t) is types.decoder(t)
    a, b = types.decode(t, v), types.decode(t, v)
    assert a == b == v and a is not v and a["walk"] is not v["walk"] and a["walk"] is not b["walk"]
    a["walk"].append(9)
    assert v["walk"] == [0, 2, 1]                              # the payload in the record is not altered
    u = {"record": {"walk": {"list": "integer"}, "length": "integer"}}   # an equal type, another object
    assert types.decode(u, v) == v
