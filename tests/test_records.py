"""The record of every example under the agenda, pinned by a digest.

A change of the substrate that keeps its semantics, such as an optimization, must leave every
record identical: every coordinate, every payload, every hash link, in the same order. The digests
were taken at commit 822d15c. A change that alters a record on purpose (a new field of a coordinate,
a changed example) updates the digest here and says why in its commit message.
"""
import hashlib
import json

import pytest

from conftest import EXAMPLES, ROOT, quiet
from ztes.substrate.store import MemoryStore, read
from ztes.system.system import System

PINNED = {                      # example: (events, digest of the record)
    "aco":             (73,  "449255bb3c29dce2"),
    "aco-draw":        (138, "de75462c47bef7af"),
    "agent":           (85,  "275977ab65c077bd"),   # added in 0.1.1
    "computability/halting/antihydra":             (1012, "91db8f046e3e1a14"),   # added after 0.1.2
    "computability/halting/collatz":               (1009, "0c534871d6cb5392"),   # added after 0.1.2
    "computability/halting/finish-fair":           (26,   "1768734bf6acabc2"),   # added after 0.1.2
    "computability/halting/finish-unfair":         (50,   "2f1ca06deb972113"),   # added after 0.1.2
    "computability/halting/finish-unreachable":    (50,   "bbcf4291e6688799"),   # added after 0.1.2
    "computability/halting/machines":              (183,  "b34659e7f8958d8b"),   # added after 0.1.2
    "dedekind-cut":    (26,  "cb2a10ba074ba456"),
    "factorization":   (27,  "7412db70b15c9f13"),
    "payment":         (21,  "93eab31cd4750c1f"),
    "physics/absorbing-walk/bright":    (52,  "eb2877635c0da683"),   # added after 0.1.2
    "physics/absorbing-walk/dark":      (53,  "0ebb500a5a75349b"),   # added after 0.1.2
    "physics/absorbing-walk/dephasing": (76,  "c65b4d6f0416b80d"),   # added after 0.1.2
    "physics/path-sums/barrier":      (237, "697c69821b4e496d"),   # added after 0.1.2
    "physics/path-sums/checkerboard": (50,  "ea260db8d38fef00"),   # added after 0.1.2
    "physics/path-sums/two-slits":    (89,  "3f029aeb116dc81a"),   # added after 0.1.2
    "prime-witnesses": (26,  "912bd79788754d47"),
    "sqrt2":           (16,  "2ac1e04d3a666ca2"),
    "tsp":             (468, "2f197520f400df1c"),
    "tsp-bnb":         (71,  "0ac6d3fa72f98c17"),
}


def digest(C):
    """The first 16 hexadecimal digits of SHA-256 over the canonical JSON of the whole record."""
    text = json.dumps(C, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def test_every_example_is_pinned():
    assert sorted(PINNED) == EXAMPLES


@pytest.mark.parametrize("name", sorted(PINNED))
def test_the_record_is_the_pinned_one(name):
    system, store = System(ROOT / "examples" / name), MemoryStore()
    system.run(store, log=quiet)
    C = list(read(store))
    assert (len(C), digest(C)) == PINNED[name]
