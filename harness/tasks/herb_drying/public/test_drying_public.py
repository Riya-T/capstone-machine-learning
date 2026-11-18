"""Public checks for drying.py.

Usage (with drying.py importable, e.g. in the sandbox):
    python -m pytest public/test_drying_public.py
"""

import pytest
from drying import DryingRoom, NotEnoughBundles


@pytest.fixture
def room():
    r = DryingRoom()
    r.add_rack("north")
    r.add_rack("south")
    return r


def test_hanging_and_taking_down_change_the_count(room):
    room.hang("north", "sage", 5)
    room.hang("north", "sage", 2)
    room.take_down("north", "sage", 3)
    assert room.get_count("north", "sage") == 4
    assert room.get_count("north", "mint") == 0


def test_taking_down_more_than_there_are_raises(room):
    room.hang("north", "sage", 5)
    with pytest.raises(NotEnoughBundles):
        room.take_down("north", "sage", 6)
    assert room.get_count("north", "sage") == 5


def test_herbs_are_listed_in_alphabetical_order(room):
    room.hang("north", "thyme", 1)
    room.hang("north", "basil", 2)
    room.hang("north", "mint", 3)
    assert room.get_herbs("north") == ["basil", "mint", "thyme"]


def test_shift_all_moves_every_herb_and_returns_how_many(room):
    room.hang("north", "sage", 5)
    room.hang("north", "mint", 2)
    room.hang("south", "dill", 1)
    assert room.shift_all("north", "south") == 7
    assert room.get_herbs("north") == []
    assert room.get_count("north", "sage") == 0
    assert room.get_herbs("south") == ["dill", "mint", "sage"]
    assert room.get_racks() == ["north", "south"]


def test_a_dismantled_rack_is_gone(room):
    room.hang("north", "sage", 5)
    room.hang("south", "sage", 1)
    assert room.dismantle_rack("north", "south") == 5
    assert room.get_racks() == ["south"]
    assert room.get_count("south", "sage") == 6
    with pytest.raises(KeyError):
        room.get_count("north", "sage")
    with pytest.raises(KeyError):
        room.hang("north", "sage", 1)


def test_dismantling_an_empty_rack_returns_0_and_frees_its_name(room):
    assert room.dismantle_rack("south", "north") == 0
    assert room.get_racks() == ["north"]
    room.add_rack("south")
    assert room.get_racks() == ["north", "south"]
    assert room.get_herbs("south") == []
