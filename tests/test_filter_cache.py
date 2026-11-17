"""A filter that reads only x is decided once per event and kept in the index (epistemic._qualifying).

Every test compares the binding as it is now evaluated with the binding evaluated the way it was
before the cache, by a filter that the cache does not take (_reads_only_x false): the same values,
for every select, window and prefix, in any order of reading, and the same errors.
"""
import random

import pytest

from ztes.model import epistemic as context, language
from ztes.model.view import Index, Record


def record(payloads, lineages=("a", "b")):
    rnd = random.Random(7)
    events = [{"coord": {"kind": "exec", "abstraction": rnd.choice(lineages)}, "payload": p} for p in payloads]
    ix = Index()
    for n, e in enumerate(events):
        ix.add(n, e)
    return Record(events, len(events), ix)


def payloads(count, seed):
    rnd = random.Random(seed)
    return [{"k": rnd.choice("abc"), "v": rnd.randint(-5, 20), "l": [rnd.randint(0, 9) for _ in range(rnd.randint(0, 4))]}
            for _ in range(count)]


TYPE = {"record": {"k": "text", "v": "integer", "l": {"list": "integer"}}}
STATIC = ["x['v'] % 3 == 0", "x['k'] == 'a'", "len(x['l']) > 2", "max(x['l'] + [0]) > 5", "x['v'] > 0 and x['k'] != 'c'"]
SELECTS = ["all", "count", "exists", "last", "first"]


def uncached(*args):
    """The binding through the path that does not keep the qualifying events."""
    saved = context._reads_only_x
    context._reads_only_x = lambda *a: False
    try:
        return context.bind(*args)
    finally:
        context._reads_only_x = saved


def evaluate(C, b, env=None, ns=language.SAFE):
    try:
        return ("value", context.bind(C, "b", b, env or {}, ns))
    except Exception as x:
        return ("error", type(x).__name__)


def evaluate_uncached(C, b, env=None, ns=language.SAFE):
    try:
        return ("value", uncached(C, "b", b, env or {}, ns))
    except Exception as x:
        return ("error", type(x).__name__)


@pytest.mark.parametrize("seed", range(6))
def test_the_cached_filter_gives_what_the_uncached_one_gives(seed):
    rnd = random.Random(seed)
    C = record(payloads(60, seed))
    assert all(context._reads_only_x(where, {}, language.SAFE) for where in STATIC)
    for where in STATIC:
        for sel in SELECTS:
            for window in (None, 1, 3):
                if window and sel != "all":
                    continue
                b = {"from": rnd.choice(["a", "b", ["a", "b"]]), "select": sel, "type": TYPE, "where": where}
                if window:
                    b["window"] = window
                if sel in ("last", "first"):
                    b["default"] = {"k": "z", "v": 0, "l": []}
                order = list(range(len(C) + 1))
                rnd.shuffle(order)                            # prefixes read in any order: longer, then shorter
                for n in order:
                    assert evaluate(C[:n], b) == evaluate_uncached(C[:n], b), (where, sel, window, n)
    kept = [k for k in C.index.memo if k[0] == "where"]
    assert len(kept) >= len(STATIC)                           # the cached path was taken


def test_a_filter_that_reads_a_constant_or_a_binding_is_not_cached():
    C = record(payloads(30, 1))
    env = {"LIMIT": 4, "earlier": 2}
    for where in ("x['v'] > LIMIT", "x['v'] > earlier", "len(x['l']) > LIMIT - earlier"):
        assert not context._reads_only_x(where, env, language.SAFE)
        b = {"from": ["a", "b"], "select": "all", "type": TYPE, "where": where}
        for n in range(len(C) + 1):
            assert evaluate(C[:n], b, env) == evaluate_uncached(C[:n], b, env)
    assert context._reads_only_x("len(x['l']) > 2", env, language.SAFE)
    assert not context._reads_only_x("len(x['l']) > 2", {"len": 1}, language.SAFE)    # env before the namespace
    assert not context._reads_only_x("unknown(x)", {}, language.SAFE)                 # left to fail as before


def test_two_libraries_with_the_same_filter_text_are_kept_apart():
    C = record(payloads(40, 2))
    small = language.namespace("def f(x):\n    return x['v'] < 5\n")
    large = language.namespace("def f(x):\n    return x['v'] > 5\n")
    b = {"from": ["a", "b"], "select": "all", "type": TYPE, "where": "f(x)"}
    assert context._reads_only_x("f(x)", {}, small)
    for n in (40, 20, 40):
        one, two = evaluate(C[:n], b, ns=small), evaluate(C[:n], b, ns=large)
        assert one == evaluate_uncached(C[:n], b, ns=small) and two == evaluate_uncached(C[:n], b, ns=large)
        assert one != two


def test_a_filter_that_fails_leaves_the_index_as_it_was():
    """x['v'] // x['d'] fails at the event whose d is 0: every prefix that contains it fails, as
    before, and the prefixes before it keep their values whatever was read in between."""
    p = [{"v": i, "d": 0 if i == 5 else 1} for i in range(10)]
    C = record(p, lineages=("a",))
    t = {"record": {"v": "integer", "d": "integer"}}
    b = {"from": "a", "select": "all", "type": t, "where": "x['v'] // x['d'] >= 2"}
    for n in (3, 10, 4, 6, 5, 10, 2):
        assert evaluate(C[:n], b) == evaluate_uncached(C[:n], b), n
    assert evaluate(C[:5], b) == ("value", [{"v": 2, "d": 1}, {"v": 3, "d": 1}, {"v": 4, "d": 1}])
    assert evaluate(C[:6], b)[0] == "error"


def test_every_read_gives_new_values():
    """The values are decoded at every read, as before: a body that alters one cannot alter the next."""
    C = record(payloads(10, 3), lineages=("a",))
    b = {"from": "a", "select": "all", "type": TYPE, "where": "x['v'] > -10"}
    first = context.bind(C, "b", b, {}, language.SAFE)
    first[0]["l"].append(99)
    second = context.bind(C, "b", b, {}, language.SAFE)
    assert second[0]["l"] != first[0]["l"] and second == evaluate_uncached(C, b)[1]
