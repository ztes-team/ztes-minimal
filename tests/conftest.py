"""Shared fixtures of the tests: example paths, a quiet log, a small system written on the fly."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))                # so that tests can import this module

from ztes.system.system import System

ROOT = Path(__file__).parent.parent
SQRT2 = ROOT / "examples" / "sqrt2"
FACTOR = ROOT / "examples" / "factorization"
COUNTER = Path(__file__).parent / "systems" / "counter"
quiet = lambda *_: None


@pytest.fixture
def system():
    """The √2 system, used by many tests of the substrate."""
    return System(SQRT2)


def make_system(tmp_path, system_json, files):
    """Write a small system to a temporary directory and load it."""
    root = tmp_path / "sys"
    (root / "abstractions").mkdir(parents=True)
    (root / "system.json").write_text(json.dumps(system_json))
    (root / "DESIGN.md").write_text("test")
    for rel, content in files.items():
        f = root / "abstractions" / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(content))
    return System(root)
