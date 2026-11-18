"""Hidden tests for the initial herb_drying spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with drying.py importable, e.g. in the sandbox):
    python -m pytest private/test_drying_initial.py
"""

import pytest
from drying import DryingError, DryingRoom, NotEnoughBundles

BAD_COUNTS = [0, -3]


@pytest.fixture
def room():
    r = DryingRoom()
    for name in ["north", "south", "east"]:
        r.add_rack(name)
    r.hang("north", "sage", 5)
    r.hang("north", "mint", 2)
    return r


def state(r):
    """Every rack in order with its herbs and counts, to check that a failed
    call changed nothing."""
    return [(k, [(h, r.get_count(k, h)) for h in r.get_herbs(k)]) for k in r.get_racks()]


# --- racks --------------------------------------------------------------------


def test_a_new_rack_is_empty():
    r = DryingRoom()
    r.add_rack("north")
    assert r.get_herbs("north") == []
    assert r.get_count("north", "sage") == 0


def test_racks_are_listed_in_the_order_added():
    r = DryingRoom()
    for name in ["west", "north", "east"]:
        r.add_rack(name)
    assert r.get_racks() == ["west", "north", "east"]


def test_adding_a_name_in_use_is_rejected(room):
    before = state(room)
    with pytest.raises(DryingError):
        room.add_rack("north")
    assert state(room) == before


def test_a_dismantled_name_can_be_added_again_as_a_new_empty_rack(room):
    room.dismantle_rack("north", "east")
    room.add_rack("north")
    assert room.get_racks() == ["south", "east", "north"]
    assert room.get_herbs("north") == []
    assert room.get_count("north", "sage") == 0
    assert room.get_count("east", "sage") == 5


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.hang("west", "sage", 1),
        lambda r: r.take_down("west", "sage", 1),
        lambda r: r.shift_all("west", "south"),
        lambda r: r.shift_all("north", "west"),
        lambda r: r.dismantle_rack("west", "south"),
        lambda r: r.dismantle_rack("north", "west"),
        lambda r: r.get_count("west", "sage"),
        lambda r: r.get_herbs("west"),
    ],
)
def test_racks_that_are_not_in_use_raise_key_error(room, call):
    before = state(room)
    with pytest.raises(KeyError):
        call(room)
    assert state(room) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.hang("east", "sage", 1),
        lambda r: r.take_down("east", "sage", 1),
        lambda r: r.shift_all("north", "east"),
        lambda r: r.dismantle_rack("east", "north"),
        lambda r: r.dismantle_rack("north", "east"),
        lambda r: r.get_count("east", "sage"),
        lambda r: r.get_herbs("east"),
    ],
)
def test_a_dismantled_rack_is_not_in_use(room, call):
    room.dismantle_rack("east", "south")  # east is empty
    before = state(room)
    with pytest.raises(KeyError):
        call(room)
    assert state(room) == before


# --- hanging and taking down --------------------------------------------------


def test_hanging_and_taking_down_change_the_count(room):
    room.hang("north", "sage", 3)
    room.take_down("north", "sage", 6)
    room.hang("south", "sage", 1)
    assert room.get_count("north", "sage") == 2
    assert room.get_count("south", "sage") == 1
    assert room.get_count("north", "mint") == 2


def test_every_bundle_of_a_herb_can_be_taken_down(room):
    room.take_down("north", "mint", 2)
    assert room.get_count("north", "mint") == 0
    assert room.get_herbs("north") == ["sage"]


def test_a_herb_taken_down_can_be_hung_again(room):
    room.take_down("north", "sage", 5)
    room.hang("north", "sage", 1)
    assert room.get_herbs("north") == ["mint", "sage"]
    assert room.get_count("north", "sage") == 1


def test_taking_down_more_than_there_are_raises_and_changes_nothing(room):
    before = state(room)
    with pytest.raises(NotEnoughBundles):
        room.take_down("north", "mint", 3)
    with pytest.raises(NotEnoughBundles):
        room.take_down("north", "dill", 1)
    with pytest.raises(NotEnoughBundles):
        room.take_down("south", "sage", 1)
    assert state(room) == before


def test_herbs_are_alphabetical_whatever_the_order_hung(room):
    room.hang("south", "thyme", 1)
    room.hang("south", "basil", 4)
    room.hang("south", "dill", 2)
    assert room.get_herbs("south") == ["basil", "dill", "thyme"]
    assert room.get_herbs("north") == ["mint", "sage"]


@pytest.mark.parametrize("count", BAD_COUNTS)
def test_hanging_0_or_fewer_bundles_is_rejected(room, count):
    before = state(room)
    with pytest.raises(ValueError):
        room.hang("north", "sage", count)
    with pytest.raises(ValueError):
        room.hang("south", "dill", count)
    assert state(room) == before


# --- shift_all ----------------------------------------------------------------


def test_shift_all_moves_every_herb(room):
    room.hang("south", "sage", 1)
    room.hang("south", "dill", 4)
    assert room.shift_all("north", "south") == 7
    assert room.get_herbs("north") == []
    assert room.get_herbs("south") == ["dill", "mint", "sage"]
    assert room.get_count("south", "sage") == 6
    assert room.get_count("south", "mint") == 2
    assert room.get_racks() == ["north", "south", "east"]


def test_a_shifted_rack_stays_in_use(room):
    room.shift_all("north", "east")
    room.hang("north", "dill", 1)
    assert room.get_herbs("north") == ["dill"]
    assert room.shift_all("east", "north") == 7
    assert room.get_count("north", "sage") == 5


# --- dismantle_rack -----------------------------------------------------------


def test_dismantle_rack_moves_every_bundle_and_removes_it(room):
    room.hang("east", "sage", 2)
    assert room.dismantle_rack("north", "east") == 7
    assert room.get_racks() == ["south", "east"]
    assert room.get_count("east", "sage") == 7
    assert room.get_count("east", "mint") == 2


def test_dismantling_an_empty_rack_moves_nothing(room):
    assert room.dismantle_rack("south", "north") == 0
    assert room.get_racks() == ["north", "east"]
    assert room.get_count("north", "sage") == 5


def test_the_other_racks_keep_their_order_after_a_dismantle(room):
    room.add_rack("west")
    room.dismantle_rack("south", "west")
    assert room.get_racks() == ["north", "east", "west"]


def test_shifting_a_rack_onto_itself_is_rejected(room):
    before = state(room)
    with pytest.raises(ValueError):
        room.shift_all("north", "north")
    assert state(room) == before


# --- general ------------------------------------------------------------------


def test_not_enough_bundles_is_a_drying_error():
    assert issubclass(NotEnoughBundles, DryingError)


def test_rooms_do_not_share_racks():
    first, second = DryingRoom(), DryingRoom()
    first.add_rack("north")
    first.hang("north", "sage", 3)
    assert second.get_racks() == []
    second.add_rack("north")
    assert second.get_count("north", "sage") == 0
