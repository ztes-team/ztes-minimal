"""The two modes of the replay (substrate/replay.py): the full replay re-derives every candidate and
re-judges it; with judgments_only the recorded candidate is re-judged as it stands.

On a sound record both find nothing. On the eight defective records of Table 5 (ztes defects) the
faster mode finds the same seven defects, at the same events, and misses the third, whose draws were
never recorded: the candidate is admissible, but does not follow from the record. That is what the
module docstring says the mode does not check.
"""
import pytest

from conftest import EXAMPLES, ROOT, quiet
from ztes import defects
from ztes.substrate.replay import verify
from ztes.substrate.store import MemoryStore, read
from ztes.system.system import System


@pytest.mark.parametrize("name", EXAMPLES)
def test_a_sound_record_passes_both_modes(name):
    system, store = System(ROOT / "examples" / name), MemoryStore()
    system.run(store, log=quiet)
    C = read(store)
    assert verify(C) == [] and verify(C, judgments_only=True) == []


def test_the_faster_mode_finds_every_defect_but_the_hidden_draw():
    """Seven defects are found at the same event. The overwritten tour of the first is found one
    event later, by the hash link of the event after it, as the README says of that case."""
    for k, (condition, defect) in enumerate(defects.DEFECTS, 1):
        C = defect()
        full, judged = verify(C), verify(C, judgments_only=True)
        assert full, condition                                  # the full replay finds every defect
        if condition == "recorded inputs (S1.2)":
            assert judged == []                                 # admissible candidates that do not follow from C
        elif condition == "append-only (S1.1)":
            assert judged[0][0] == full[0][0] + 1 and "hash link" in judged[0][1]
        else:
            assert judged[0][0] == full[0][0], condition
