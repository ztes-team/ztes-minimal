"""A frozen binding ("select": "all", "frozen": true): every value decoded once, frozen and kept in the
index, shared by every read (epistemic._frozen).

The values must be those of the same binding without "frozen", each frozen (lists become tuples,
records read-only mappings), for every prefix read in any order, with a filter and a window; they
must be shared and immutable; τ_root must refuse a frozen binding whose filter reads another
binding, and "frozen" outside select "all"; and a system that reads its history through a frozen
binding must run and replay to the same values as without it.
"""
import random

import pytest

from conftest import make_system, quiet
from test_filter_cache import TYPE, payloads, record
from ztes.model import epistemic as context, language
from ztes.model.epistemic import freeze
from ztes.substrate.governance import refusal
from ztes.substrate.replay import verify
from ztes.substrate.store import MemoryStore, read


def frozen_read(C, b, env=None, key="k"):
    return context.bind(C, "b", dict(b, frozen=True), env or {}, language.SAFE, key)


def plain_read(C, b, env=None):
    return context.bind(C, "b", b, env or {}, language.SAFE)


@pytest.mark.parametrize("seed", range(5))
def test_the_values_are_those_of_the_plain_binding_frozen(seed):
    rnd = random.Random(seed)
    C = record(payloads(50, seed))
    env = {"LIMIT": 3}                                         # a constant: allowed in the filter of a frozen binding
    for n_where, where in enumerate([None, "x['v'] % 3 == 0", "len(x['l']) > LIMIT - 1", "x['k'] != 'c'"]):
        for window in (None, 1, 4):
            b = {"from": rnd.choice(["a", "b", ["a", "b"]]), "select": "all", "type": TYPE}
            if where:
                b["where"] = where
            if window:
                b["window"] = window
            key = f"k{seed}-{n_where}-{window}-{b['from']}"
            order = list(range(len(C) + 1))
            rnd.shuffle(order)
            for n in order:
                got = frozen_read(C[:n], b, env, key)
                assert isinstance(got, tuple)
                assert got == tuple(freeze(x) for x in plain_read(C[:n], b, env)), (where, window, n)


def test_the_values_are_shared_and_immutable():
    C = record(payloads(10, 1), lineages=("a",))
    b = {"from": "a", "select": "all", "type": TYPE}
    one, two = frozen_read(C, b), frozen_read(C, b)
    assert all(x is y for x, y in zip(one, two))               # decoded once, shared by every read
    assert isinstance(one[0]["l"], tuple)
    with pytest.raises(TypeError):
        one[0]["v"] = 1                                        # a record is read-only
    with pytest.raises(AttributeError):
        one[0]["l"].append(1)                                  # a list is a tuple
    assert frozen_read(C[:4], b) == one[:4]                    # an earlier prefix: the first values only


def test_a_filter_that_fails_leaves_the_index_as_it_was():
    p = [{"v": i, "d": 0 if i == 5 else 1} for i in range(10)]
    C = record(p, lineages=("a",))
    b = {"from": "a", "select": "all", "type": {"record": {"v": "integer", "d": "integer"}},
         "where": "x['v'] // x['d'] >= 2"}
    for n in (3, 10, 4, 6, 5, 10, 2):
        try:
            got = ("value", frozen_read(C[:n], b, key="fail"))
        except Exception as x:
            got = ("error", type(x).__name__)
        try:
            want = ("value", tuple(freeze(x) for x in plain_read(C[:n], b)))
        except Exception as x:
            want = ("error", type(x).__name__)
        assert got == want, n


def specification(binding):
    return {"abstraction": "a", "role": "criterion", "version": 1, "returns": "boolean", "total": True,
            "constants": {"LIMIT": 2},
            "inputs": {"context": {"k": {"from": "a", "select": "count"}, "h": binding},
                       "candidate": {"name": "w", "type": "integer"}},
            "body": {"result": "True"}}


def test_tau_root_checks_a_frozen_binding():
    ok = {"from": "a", "select": "all", "frozen": True, "where": "x > LIMIT"}
    assert refusal([], specification(ok)) is None
    assert "may use only x" in refusal([], specification(dict(ok, where="x > k")))        # reads a binding
    assert 'belongs to select "all"' in refusal([], specification(dict(ok, select="last", default=0)))
    assert "true or false" in refusal([], specification(dict(ok, frozen="yes")))
    assert refusal([], specification(dict(ok, frozen=False, where="x > k"))) is None       # not frozen: as before


def history_system(tmp_path, frozen):
    """a records six steps; b, once all six exist, records a sum over the even ones, read as history."""
    history = {"from": "a", "select": "all", "type": "A", "where": "x['i'] % 2 == 0"}
    if frozen:
        history["frozen"] = True
    return make_system(tmp_path, {
        "system": "h", "abstractions": ["a", "b"],
        "types": {"A": {"record": {"i": "integer", "l": {"list": "integer"}}}},
        "constants": {"K": 6},
        "bindings": {"k": {"from": "$self", "select": "count"}, "history": history},
    }, {
        "a/criterion.v1.json": {"inputs": {"context": ["k"], "candidate": {"name": "w", "type": "A"}},
                                "body": {"result": "w['i'] == k and k < K and w['l'] == [k, k + 1]"}},
        "a/ontology.v1.json": {"inputs": {"context": ["k"]}, "returns": "A",
                               "body": {"result": "None if k >= K else {'i': k, 'l': [k, k + 1]}"}},
        "b/criterion.v1.json": {"inputs": {"context": ["k", "history"], "candidate": {"name": "w", "type": "integer"}},
                                "body": {"result": "k == 0 and w == sum(sum(x['l']) for x in history)"}},
        "b/ontology.v1.json": {"requires": {"a": "K"}, "inputs": {"context": ["k", "history"]}, "returns": "integer",
                               "body": {"result": "None if k else sum(sum(x['l']) for x in history)"}},
    })


def test_a_system_reads_its_history_frozen_and_replays(tmp_path):
    out = {}
    for frozen in (False, True):
        system, store = history_system(tmp_path / str(frozen), frozen), MemoryStore()
        system.run(store, log=quiet)
        C = list(read(store))
        assert verify(C) == []
        out[frozen] = [e["payload"] for e in C if e["coord"]["kind"] == "exec"]
    assert out[True] == out[False] and out[True][-1] == 15     # (0 + 1) + (2 + 3) + (4 + 5)
