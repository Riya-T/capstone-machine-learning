"""Hidden tests for the c_capacity change (rack capacities). Never shown to
the writer or the editor.

Usage (with drying.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from drying import DryingError, DryingRoom, NotEnoughBundles, RackFull

BAD_CAPACITIES = [0, -2]


@pytest.fixture
def room():
    r = DryingRoom()
    for name in ["north", "south", "east"]:
        r.add_rack(name)
    r.hang("north", "sage", 3)
    r.hang("north", "mint", 2)
    r.hang("south", "dill", 4)
    return r


def state(r):
    return [(k, [(h, r.get_count(k, h)) for h in r.get_herbs(k)]) for k in r.get_racks()]


# --- the setting ------------------------------------------------------------


def test_every_rack_starts_without_a_capacity(room):
    assert [room.get_capacity(k) for k in room.get_racks()] == [None, None, None]
    room.add_rack("west")
    assert room.get_capacity("west") is None
    room.hang("west", "sage", 500)
    assert room.get_count("west", "sage") == 500


def test_a_rack_added_again_after_dismantling_has_no_capacity(room):
    room.set_capacity("east", 3)
    room.dismantle_rack("east", "south")
    room.add_rack("east")
    assert room.get_capacity("east") is None
    room.hang("east", "basil", 10)
    assert room.get_count("east", "basil") == 10


def test_each_setting_replaces_the_one_before(room):
    room.set_capacity("east", 2)
    room.set_capacity("east", 5)
    assert room.get_capacity("east") == 5
    room.hang("east", "basil", 5)
    room.set_capacity("east", None)
    assert room.get_capacity("east") is None
    room.hang("east", "basil", 5)
    assert room.get_count("east", "basil") == 10


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_capacities_of_0_or_less_are_rejected_and_keep_the_old_one(room, capacity):
    room.set_capacity("south", 8)
    with pytest.raises(ValueError):
        room.set_capacity("south", capacity)
    assert room.get_capacity("south") == 8


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.set_capacity("west", 5),
        lambda r: r.get_capacity("west"),
        lambda r: r.set_capacity("east", 5),  # dismantled below
        lambda r: r.get_capacity("east"),
    ],
)
def test_racks_not_in_use_raise_key_error(room, call):
    room.dismantle_rack("east", "south")
    with pytest.raises(KeyError):
        call(room)


def test_a_setting_changes_no_counts(room):
    before = state(room)
    room.set_capacity("north", 1)
    room.set_capacity("east", 7)
    assert state(room) == before


# --- hang -----------------------------------------------------------------------


def test_the_capacity_counts_every_herb_together(room):
    room.set_capacity("north", 8)
    room.hang("north", "basil", 2)
    before = state(room)
    with pytest.raises(RackFull):
        room.hang("north", "thyme", 2)
    assert state(room) == before


def test_filling_a_rack_exactly_is_allowed(room):
    room.set_capacity("east", 4)
    room.hang("east", "basil", 4)
    assert room.get_count("east", "basil") == 4
    with pytest.raises(RackFull):
        room.hang("east", "basil", 1)


def test_a_capacity_only_applies_to_its_own_rack(room):
    room.set_capacity("east", 1)
    room.hang("south", "dill", 10)
    assert room.get_count("south", "dill") == 14


# --- shift_all and dismantle_rack ---------------------------------------------


def test_shift_all_onto_a_rack_with_room(room):
    room.set_capacity("south", 9)
    assert room.shift_all("north", "south") == 5
    assert room.get_herbs("south") == ["dill", "mint", "sage"]


def test_shift_all_onto_a_rack_without_room_moves_nothing(room):
    room.set_capacity("south", 8)
    before = state(room)
    with pytest.raises(RackFull):
        room.shift_all("north", "south")
    assert state(room) == before


def test_dismantle_rack_into_a_rack_with_room(room):
    room.set_capacity("east", 5)
    assert room.dismantle_rack("north", "east") == 5
    assert room.get_racks() == ["south", "east"]


def test_dismantle_rack_into_a_rack_without_room_moves_nothing_and_keeps_it(room):
    room.set_capacity("east", 4)
    before = state(room)
    with pytest.raises(RackFull):
        room.dismantle_rack("north", "east")
    assert state(room) == before
    assert room.get_racks() == ["north", "south", "east"]


def test_a_refused_dismantle_can_be_retried_with_a_larger_capacity(room):
    room.set_capacity("south", 6)
    with pytest.raises(RackFull):
        room.dismantle_rack("north", "south")
    room.set_capacity("south", 9)
    assert room.dismantle_rack("north", "south") == 5
    assert room.get_count("south", "sage") == 3


def test_the_capacity_of_the_rack_bundles_leave_is_not_checked(room):
    room.set_capacity("north", 1)
    assert room.shift_all("north", "east") == 5
    room.set_capacity("east", 2)
    room.take_down("east", "sage", 1)
    assert room.dismantle_rack("east", "south") == 4
    assert room.get_count("south", "sage") == 2


# --- bundles already there ------------------------------------------------------


def test_a_capacity_below_the_bundles_held_keeps_them(room):
    room.set_capacity("north", 2)  # north holds 5 bundles
    assert room.get_count("north", "sage") == 3
    assert room.get_herbs("north") == ["mint", "sage"]
    with pytest.raises(RackFull):
        room.hang("north", "basil", 1)
    with pytest.raises(RackFull):
        room.shift_all("south", "north")
    room.take_down("north", "mint", 2)
    room.take_down("north", "sage", 2)
    room.hang("north", "basil", 1)
    assert room.get_herbs("north") == ["basil", "sage"]
    with pytest.raises(RackFull):
        room.hang("north", "basil", 1)


def test_take_down_never_checks_the_capacity(room):
    room.set_capacity("south", 1)
    room.take_down("south", "dill", 2)
    assert room.get_count("south", "dill") == 2


# --- errors -------------------------------------------------------------------


def test_rack_full_is_a_drying_error_but_not_not_enough_bundles():
    assert issubclass(RackFull, DryingError)
    assert not issubclass(RackFull, NotEnoughBundles)


# --- undo -----------------------------------------------------------------------


def test_undoing_set_capacity_gives_back_the_old_capacity(room):
    room.set_capacity("east", 3)
    room.set_capacity("east", 10)
    room.undo()
    assert room.get_capacity("east") == 3
    room.undo()
    assert room.get_capacity("east") is None
    room.hang("east", "basil", 20)
    assert room.get_count("east", "basil") == 20


def test_undoing_a_hang_keeps_the_capacity(room):
    room.set_capacity("east", 3)
    room.hang("east", "basil", 3)
    room.undo()
    assert room.get_herbs("east") == []
    assert room.get_capacity("east") == 3
    with pytest.raises(RackFull):
        room.hang("east", "basil", 4)


def test_an_undone_dismantle_brings_the_rack_back_with_its_capacity(room):
    room.set_capacity("north", 7)
    room.dismantle_rack("north", "east")
    room.undo()
    assert room.get_capacity("north") == 7
    assert room.get_count("north", "sage") == 3
    with pytest.raises(RackFull):
        room.hang("north", "sage", 3)


def test_failed_calls_on_full_racks_are_not_recorded(room):
    room.set_capacity("south", 4)
    for call in (
        lambda: room.hang("south", "dill", 1),
        lambda: room.shift_all("north", "south"),
        lambda: room.dismantle_rack("north", "south"),
    ):
        with pytest.raises(RackFull):
            call()
    room.undo()  # the capacity
    assert room.get_capacity("south") is None
    assert room.get_count("south", "dill") == 4
