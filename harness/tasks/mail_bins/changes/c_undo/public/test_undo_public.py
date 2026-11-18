"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with sorting.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from sorting import SortingError, SortingRoom


@pytest.fixture
def room():
    r = SortingRoom()
    r.add_bin("east")
    r.add_bin("west")
    return r


def test_undo_takes_back_the_last_parcel_dropped(room):
    room.drop("east", "NY-1")
    room.drop("east", "LA-2")
    room.undo()
    assert room.get_parcels("east") == ["NY-1"]
    room.undo()
    assert room.get_parcels("east") == []


def test_undo_takes_back_a_recall(room):
    room.drop("west", "NY-1")
    room.drop("west", "LA-2")
    assert room.recall("LA-2") == "west"
    room.undo()
    assert room.get_parcels("west") == ["NY-1", "LA-2"]


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(SortingError):
        SortingRoom().undo()
