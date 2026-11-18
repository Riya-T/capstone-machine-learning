"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with drying.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from drying import DryingError, DryingRoom


@pytest.fixture
def room():
    r = DryingRoom()
    r.add_rack("north")
    r.add_rack("south")
    return r


def test_undo_takes_back_the_last_hang(room):
    room.hang("north", "sage", 5)
    room.hang("north", "sage", 2)
    room.undo()
    assert room.get_count("north", "sage") == 5
    room.undo()
    assert room.get_herbs("north") == []


def test_undo_takes_back_a_take_down(room):
    room.hang("north", "mint", 4)
    room.take_down("north", "mint", 3)
    room.undo()
    assert room.get_count("north", "mint") == 4


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(DryingError):
        DryingRoom().undo()
