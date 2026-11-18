"""Public checks for the c_capacity change (rack capacities). Shown to the
editor, never to the writer.

Usage (with drying.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/public/test_capacity_public.py
"""

import pytest
from drying import DryingRoom, RackFull


@pytest.fixture
def room():
    r = DryingRoom()
    r.add_rack("north")
    r.add_rack("south")
    return r


def test_a_new_rack_has_no_capacity(room):
    assert room.get_capacity("north") is None
    room.set_capacity("north", 6)
    assert room.get_capacity("north") == 6


def test_hanging_past_the_capacity_raises(room):
    room.set_capacity("north", 6)
    room.hang("north", "sage", 4)
    with pytest.raises(RackFull):
        room.hang("north", "mint", 3)
    room.hang("north", "mint", 2)
    assert room.get_count("north", "mint") == 2
    assert room.get_count("north", "sage") == 4
