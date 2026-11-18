"""Public checks for the c_accepts change (destinations a bin accepts).
Shown to the editor, never to the writer.

Usage (with sorting.py importable, e.g. in the sandbox):
    python -m pytest changes/c_accepts/public/test_accepts_public.py
"""

import pytest
from sorting import NotAccepted, SortingRoom


@pytest.fixture
def room():
    r = SortingRoom()
    r.add_bin("east")
    r.add_bin("west")
    return r


def test_only_accepted_parcels_can_be_dropped(room):
    assert room.get_accepts("east") is None
    room.set_accepts("east", ["NY-", "BOS-"])
    assert room.get_accepts("east") == ["BOS-", "NY-"]
    room.drop("east", "NY-1")
    with pytest.raises(NotAccepted):
        room.drop("east", "LA-2")
    assert room.get_parcels("east") == ["NY-1"]


def test_emptying_into_a_bin_that_refuses_a_parcel_moves_nothing(room):
    room.drop("west", "NY-1")
    room.drop("west", "LA-2")
    room.set_accepts("east", ["NY-"])
    with pytest.raises(NotAccepted):
        room.empty_bin_into("west", "east")
    assert room.get_parcels("west") == ["NY-1", "LA-2"]
    assert room.get_parcels("east") == []
