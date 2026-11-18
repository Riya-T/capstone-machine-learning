"""Hidden tests for the c_herb_query change (looking up a herb across
racks). Never shown to the writer or the editor.

Usage (with drying.py importable, e.g. in the sandbox):
    python -m pytest changes/c_herb_query/private/test_herb_query_new.py
"""

import pytest
from drying import DryingRoom


@pytest.fixture
def room():
    r = DryingRoom()
    for name in ["north", "south", "east", "west"]:
        r.add_rack(name)
    r.hang("west", "sage", 1)
    r.hang("north", "sage", 3)
    r.hang("north", "mint", 2)
    r.hang("east", "sage", 4)
    r.hang("south", "dill", 5)
    return r


def state(r):
    return [(k, [(h, r.get_count(k, h)) for h in r.get_herbs(k)]) for k in r.get_racks()]


# --- totals -------------------------------------------------------------------


def test_the_total_adds_every_rack(room):
    assert room.get_total("sage") == 8
    assert room.get_total("mint") == 2
    assert room.get_total("dill") == 5


def test_a_herb_never_hung_has_a_total_of_0(room):
    assert room.get_total("basil") == 0


def test_the_total_follows_hanging_and_taking_down(room):
    room.hang("south", "sage", 2)
    room.take_down("east", "sage", 3)
    assert room.get_total("sage") == 7


def test_moving_bundles_keeps_the_total(room):
    room.shift_all("north", "south")
    assert room.get_total("sage") == 8
    room.dismantle_rack("east", "west")
    assert room.get_total("sage") == 8
    assert room.get_total("mint") == 2


def test_herbs_taken_down_entirely_add_nothing(room):
    room.take_down("north", "mint", 2)
    assert room.get_total("mint") == 0


# --- racks with a herb --------------------------------------------------------


def test_racks_with_a_herb_are_in_rack_order(room):
    assert room.get_racks_with("sage") == ["north", "east", "west"]
    assert room.get_racks_with("mint") == ["north"]


def test_a_herb_on_no_rack_gives_an_empty_list(room):
    assert room.get_racks_with("basil") == []


def test_a_rack_whose_bundles_were_all_taken_down_is_not_listed(room):
    room.take_down("east", "sage", 4)
    assert room.get_racks_with("sage") == ["north", "west"]
    room.take_down("north", "mint", 2)
    assert room.get_racks_with("mint") == []


def test_a_rack_shifted_away_is_not_listed(room):
    room.shift_all("north", "south")
    assert room.get_racks_with("sage") == ["south", "east", "west"]
    assert room.get_racks_with("mint") == ["south"]


def test_a_dismantled_rack_is_not_listed(room):
    room.dismantle_rack("east", "north")
    assert room.get_racks_with("sage") == ["north", "west"]
    assert room.get_total("sage") == 8


def test_a_rack_added_again_after_dismantling_moves_to_the_end(room):
    room.dismantle_rack("north", "south")
    room.add_rack("north")
    room.hang("north", "sage", 1)
    assert room.get_racks_with("sage") == ["south", "east", "west", "north"]
    assert room.get_total("sage") == 9


# --- nothing changes --------------------------------------------------------


def test_the_lookups_change_nothing(room):
    before = state(room)
    room.get_total("sage")
    room.get_total("basil")
    room.get_racks_with("sage")
    room.get_racks_with("basil")
    assert state(room) == before
    assert room.get_herbs("north") == ["mint", "sage"]
