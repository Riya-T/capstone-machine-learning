"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with farm.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from farm import Farm, FarmError


@pytest.fixture
def farm():
    f = Farm()
    f.add_paddock("north")
    f.add_paddock("south")
    return f


def test_undo_takes_back_the_last_arrival(farm):
    farm.arrive("north", "sheep", 5)
    farm.arrive("north", "sheep", 2)
    farm.undo()
    assert farm.get_count("north", "sheep") == 5
    farm.undo()
    assert farm.get_species("north") == []


def test_undo_takes_back_a_move(farm):
    farm.arrive("north", "cow", 4)
    farm.move("cow", "north", "south", 3)
    farm.undo()
    assert farm.get_count("north", "cow") == 4
    assert farm.get_count("south", "cow") == 0


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(FarmError):
        Farm().undo()
