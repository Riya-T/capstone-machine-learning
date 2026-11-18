"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from silos import SiloError, Silos


@pytest.fixture
def silos():
    s = Silos()
    s.add_silo("north")
    s.add_silo("south")
    return s


def test_undo_takes_back_the_last_load(silos):
    silos.load("north", "wheat", 40)
    silos.load("north", "wheat", 10)
    silos.undo()
    assert silos.get_tonnes("north", "wheat") == 40
    silos.undo()
    assert silos.get_grains("north") == []


def test_undo_takes_back_a_blend(silos):
    silos.load("north", "oats", 9)
    assert silos.blend_into("north", "south") == 9
    silos.undo()
    assert silos.get_tonnes("north", "oats") == 9
    assert silos.get_tonnes("south", "oats") == 0


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(SiloError):
        Silos().undo()
