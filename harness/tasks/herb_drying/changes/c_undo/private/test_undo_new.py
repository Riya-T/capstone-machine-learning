"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with drying.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from drying import DryingError, DryingRoom, NotEnoughBundles


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


# --- each call can be undone ------------------------------------------------


def test_undoing_a_hang_of_a_new_herb_unlists_it(room):
    before = state(room)
    room.hang("east", "thyme", 2)
    room.undo()
    assert state(room) == before
    assert room.get_herbs("east") == []


def test_undoing_a_hang_of_more_of_a_herb(room):
    room.hang("north", "sage", 5)
    room.undo()
    assert room.get_count("north", "sage") == 3


def test_undoing_a_partial_take_down(room):
    before = state(room)
    room.take_down("north", "sage", 1)
    room.undo()
    assert state(room) == before


def test_undoing_a_take_down_of_the_last_bundles_lists_the_herb_again(room):
    before = state(room)
    room.take_down("north", "mint", 2)
    room.undo()
    assert state(room) == before
    assert room.get_herbs("north") == ["mint", "sage"]


def test_one_undo_takes_back_a_whole_shift_all(room):
    before = state(room)
    assert room.shift_all("north", "south") == 5
    room.undo()
    assert state(room) == before
    assert room.get_herbs("south") == ["dill"]


def test_undoing_a_shift_all_onto_an_empty_rack(room):
    before = state(room)
    room.shift_all("south", "east")
    room.undo()
    assert state(room) == before
    assert room.get_herbs("east") == []


def test_one_undo_brings_a_dismantled_rack_back_with_its_bundles(room):
    before = state(room)
    assert room.dismantle_rack("north", "east") == 5
    room.undo()
    assert state(room) == before
    assert room.get_racks() == ["north", "south", "east"]
    assert room.get_count("east", "sage") == 0


def test_a_rack_brought_back_keeps_its_place_in_the_list(room):
    room.add_rack("west")
    before = state(room)
    room.dismantle_rack("south", "west")
    assert room.get_racks() == ["north", "east", "west"]
    room.undo()
    assert room.get_racks() == ["north", "south", "east", "west"]
    assert state(room) == before


def test_a_rack_brought_back_is_in_use_again(room):
    room.dismantle_rack("north", "east")
    room.undo()
    room.hang("north", "sage", 1)
    assert room.get_count("north", "sage") == 4
    with pytest.raises(DryingError):
        room.add_rack("north")
    assert room.dismantle_rack("north", "south") == 6
    assert room.get_racks() == ["south", "east"]


def test_undoing_add_rack_removes_it_and_frees_the_name(room):
    room.add_rack("west")
    room.undo()
    assert room.get_racks() == ["north", "south", "east"]
    with pytest.raises(KeyError):
        room.get_herbs("west")
    room.add_rack("west")
    assert room.get_racks() == ["north", "south", "east", "west"]
    assert room.get_herbs("west") == []


def test_undo_through_a_name_that_was_dismantled_and_added_again(room):
    room.add_rack("west")
    room.hang("west", "basil", 2)
    room.dismantle_rack("west", "east")
    room.add_rack("west")  # a new, empty west
    room.hang("west", "chive", 1)
    room.undo()  # the chive
    room.undo()  # the new west
    assert room.get_racks() == ["north", "south", "east"]
    room.undo()  # the dismantle: the old west comes back with its basil
    assert room.get_racks() == ["north", "south", "east", "west"]
    assert room.get_herbs("west") == ["basil"]
    assert room.get_count("east", "basil") == 0
    room.undo()  # the basil
    room.undo()  # the first west
    assert room.get_racks() == ["north", "south", "east"]


def test_dismantling_an_empty_rack_can_be_undone(room):
    room.hang("south", "dill", 1)
    assert room.dismantle_rack("east", "south") == 0
    room.undo()
    assert room.get_racks() == ["north", "south", "east"]
    assert room.get_count("south", "dill") == 5
    room.undo()
    assert room.get_count("south", "dill") == 4


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    r = DryingRoom()
    calls = [
        lambda: r.add_rack("north"),
        lambda: r.add_rack("south"),
        lambda: r.hang("north", "sage", 5),
        lambda: r.hang("north", "mint", 2),
        lambda: r.add_rack("east"),
        lambda: r.hang("south", "dill", 4),
        lambda: r.take_down("north", "sage", 1),
        lambda: r.shift_all("south", "east"),
        lambda: r.dismantle_rack("north", "east"),
        lambda: r.add_rack("west"),
        lambda: r.hang("west", "basil", 1),
        lambda: r.hang("south", "chive", 3),
        lambda: r.shift_all("south", "west"),
        lambda: r.dismantle_rack("west", "south"),
    ]
    states = [state(r)]
    for call in calls:
        call()
        states.append(state(r))
    assert r.get_racks() == ["south", "east"]
    assert r.get_count("east", "sage") == 4
    assert r.get_count("south", "chive") == 3
    for expected in reversed(states[:-1]):
        r.undo()
        assert state(r) == expected
    with pytest.raises(DryingError):
        r.undo()
    assert r.get_racks() == []


def test_failed_calls_are_not_recorded(room):
    room.hang("east", "thyme", 2)
    for call in (
        lambda: room.take_down("north", "sage", 99),
        lambda: room.take_down("east", "basil", 1),
        lambda: room.shift_all("north", "north"),
        lambda: room.shift_all("north", "west"),
        lambda: room.dismantle_rack("west", "south"),
        lambda: room.add_rack("north"),
        lambda: room.hang("west", "sage", 1),
        lambda: room.hang("north", "sage", 0),
    ):
        with pytest.raises((ValueError, KeyError, DryingError)):
            call()
    room.undo()  # the thyme
    assert room.get_herbs("east") == []
    assert room.get_count("north", "sage") == 3


def test_get_calls_are_not_recorded(room):
    room.hang("east", "thyme", 2)
    room.get_count("east", "thyme")
    room.get_herbs("east")
    room.get_racks()
    room.undo()
    assert room.get_herbs("east") == []
    assert room.get_count("south", "dill") == 4


def test_there_is_no_redo():
    r = DryingRoom()
    r.add_rack("north")
    r.hang("north", "sage", 3)
    r.undo()
    r.undo()
    assert r.get_racks() == []
    with pytest.raises(DryingError):
        r.undo()


def test_new_calls_after_an_undo_are_undone_first(room):
    room.hang("east", "thyme", 2)
    room.undo()
    room.hang("east", "basil", 1)
    room.undo()
    assert room.get_herbs("east") == []
    room.undo()  # the dill hung in the fixture
    assert room.get_herbs("south") == []
    assert room.get_herbs("north") == ["mint", "sage"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    r = DryingRoom()
    with pytest.raises(DryingError):
        r.undo()
    r.add_rack("north")
    r.undo()
    with pytest.raises(DryingError):
        r.undo()
    assert r.get_racks() == []
    r.add_rack("north")
    r.hang("north", "sage", 1)
    assert r.get_count("north", "sage") == 1


def test_the_whole_fixture_can_be_undone(room):
    for _ in range(6):
        room.undo()
    assert room.get_racks() == []
    with pytest.raises(DryingError):
        room.undo()


def test_undo_restores_counts_that_a_later_call_checks(room):
    room.take_down("north", "sage", 3)
    room.undo()
    room.take_down("north", "sage", 3)
    assert room.get_herbs("north") == ["mint"]
    with pytest.raises(NotEnoughBundles):
        room.take_down("north", "sage", 1)
