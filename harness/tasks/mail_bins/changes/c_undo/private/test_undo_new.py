"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with sorting.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from sorting import SortingError, SortingRoom


@pytest.fixture
def room():
    r = SortingRoom()
    for name in ["east", "west", "spare"]:
        r.add_bin(name)
    for parcel in ["NY-1", "LA-2", "NY-3"]:
        r.drop("east", parcel)
    r.drop("west", "SF-4")
    return r  # 7 recorded calls


def state(r):
    return [(b, list(r.get_parcels(b))) for b in list(r.get_bins())]


# --- each call can be undone ------------------------------------------------


def test_undo_of_drop_frees_the_parcel(room):
    before = state(room)
    room.drop("spare", "TX-7")
    room.undo()
    assert state(room) == before
    room.drop("west", "TX-7")
    assert room.get_parcels("west") == ["SF-4", "TX-7"]


def test_undo_of_pick_puts_the_parcel_back_at_the_front(room):
    before = state(room)
    assert room.pick("east") == "NY-1"
    room.undo()
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]
    assert state(room) == before
    assert room.pick("east") == "NY-1"


def test_undo_of_recall_puts_the_parcel_back_in_its_place(room):
    before = state(room)
    room.recall("LA-2")
    room.undo()
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]
    assert state(room) == before


def test_a_parcel_put_back_by_undo_is_in_its_bin_again(room):
    room.pick("east")
    room.undo()
    with pytest.raises(SortingError):
        room.drop("spare", "NY-1")
    room.recall("NY-3")
    room.undo()
    with pytest.raises(SortingError):
        room.drop("west", "NY-3")
    assert room.recall("NY-3") == "east"


def test_undo_of_empty_bin_into_restores_both_bins(room):
    before = state(room)
    assert room.empty_bin_into("east", "west") == 3
    room.undo()
    assert state(room) == before
    assert room.get_parcels("west") == ["SF-4"]
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]


def test_undo_of_empty_bin_into_an_empty_bin(room):
    before = state(room)
    room.empty_bin_into("west", "spare")
    room.undo()
    assert state(room) == before
    assert room.get_parcels("spare") == []


def test_undo_of_close_bin_brings_it_back_with_its_parcels(room):
    before = state(room)
    assert room.close_bin("east", "west") == 3
    room.undo()
    assert state(room) == before
    assert room.get_bins() == ["east", "west", "spare"]
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]
    assert room.get_parcels("west") == ["SF-4"]


def test_undo_of_close_bin_keeps_its_place_in_the_list(room):
    room.add_bin("north")
    before = state(room)
    room.close_bin("west", "north")
    assert room.get_bins() == ["east", "spare", "north"]
    room.undo()
    assert room.get_bins() == ["east", "west", "spare", "north"]
    assert state(room) == before


def test_a_bin_brought_back_is_in_use_again(room):
    room.close_bin("east", "spare")
    room.undo()
    room.drop("east", "TX-7")
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3", "TX-7"]
    with pytest.raises(SortingError):
        room.add_bin("east")
    assert room.pick("east") == "NY-1"
    assert room.get_parcels("spare") == []


def test_undo_of_add_bin_removes_it_and_frees_the_name(room):
    room.add_bin("north")
    room.undo()
    assert room.get_bins() == ["east", "west", "spare"]
    with pytest.raises(KeyError):
        room.get_parcels("north")
    room.add_bin("north")
    assert room.get_bins() == ["east", "west", "spare", "north"]
    assert room.get_parcels("north") == []


def test_undo_through_a_name_that_was_closed_and_added_again(room):
    room.add_bin("north")
    room.drop("north", "TX-7")
    room.close_bin("north", "spare")
    room.add_bin("north")  # a new, empty north
    room.drop("north", "AZ-8")
    room.undo()  # AZ-8
    room.undo()  # the new north
    assert room.get_bins() == ["east", "west", "spare"]
    room.undo()  # the close: the old north comes back with TX-7
    assert room.get_bins() == ["east", "west", "spare", "north"]
    assert room.get_parcels("north") == ["TX-7"]
    assert room.get_parcels("spare") == []
    room.undo()  # TX-7
    room.undo()  # the first north
    assert room.get_bins() == ["east", "west", "spare"]


# --- calls that move nothing ------------------------------------------------


def test_an_empty_bin_into_of_nothing_is_still_a_call(room):
    room.drop("spare", "TX-7")
    room.pick("spare")
    assert room.empty_bin_into("spare", "east") == 0
    room.undo()  # the empty_bin_into, which changed nothing
    assert room.get_parcels("spare") == []
    room.undo()  # the pick
    assert room.get_parcels("spare") == ["TX-7"]


def test_closing_an_empty_bin_can_be_undone(room):
    room.drop("west", "TX-7")
    assert room.close_bin("spare", "west") == 0
    room.undo()
    assert room.get_bins() == ["east", "west", "spare"]
    assert room.get_parcels("west") == ["SF-4", "TX-7"]
    room.undo()
    assert room.get_parcels("west") == ["SF-4"]


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    r = SortingRoom()
    calls = [
        lambda: r.add_bin("east"),
        lambda: r.add_bin("west"),
        lambda: r.drop("east", "NY-1"),
        lambda: r.drop("east", "LA-2"),
        lambda: r.drop("west", "SF-4"),
        lambda: r.drop("east", "NY-3"),
        lambda: r.add_bin("spare"),
        lambda: r.pick("east"),
        lambda: r.drop("spare", "TX-7"),
        lambda: r.recall("LA-2"),
        lambda: r.empty_bin_into("east", "spare"),
        lambda: r.close_bin("west", "spare"),
        lambda: r.add_bin("west"),
        lambda: r.drop("west", "NY-1"),
        lambda: r.pick("spare"),
        lambda: r.close_bin("east", "west"),
    ]
    states = [state(r)]
    for call in calls:
        call()
        states.append(state(r))
    assert r.get_bins() == ["spare", "west"]
    assert r.get_parcels("west") == ["NY-1"]
    for expected in reversed(states[:-1]):
        r.undo()
        assert state(r) == expected
    with pytest.raises(SortingError):
        r.undo()
    assert r.get_bins() == []


def test_failed_calls_are_not_recorded(room):
    room.drop("spare", "TX-7")
    for call in (
        lambda: room.add_bin("east"),
        lambda: room.drop("west", "NY-1"),
        lambda: room.drop("north", "AZ-8"),
        lambda: room.pick("north"),
        lambda: room.recall("AZ-8"),
        lambda: room.empty_bin_into("east", "east"),
        lambda: room.close_bin("east", "north"),
    ):
        with pytest.raises((ValueError, KeyError, SortingError)):
            call()
    room.empty_bin_into("spare", "west")
    room.undo()  # the empty_bin_into
    room.undo()  # TX-7
    assert room.get_parcels("spare") == []
    assert room.get_parcels("west") == ["SF-4"]
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]


def test_a_pick_from_an_empty_bin_is_not_recorded(room):
    room.drop("west", "TX-7")
    with pytest.raises(SortingError):
        room.pick("spare")
    room.undo()  # TX-7
    assert room.get_parcels("west") == ["SF-4"]


def test_get_calls_are_not_recorded(room):
    room.drop("spare", "TX-7")
    room.get_parcels("spare")
    room.get_bins()
    room.undo()
    assert room.get_parcels("spare") == []
    assert room.get_parcels("west") == ["SF-4"]


def test_there_is_no_redo():
    r = SortingRoom()
    r.add_bin("east")
    r.drop("east", "NY-1")
    r.undo()
    r.undo()
    assert r.get_bins() == []
    with pytest.raises(SortingError):
        r.undo()


def test_new_calls_after_an_undo_are_undone_first(room):
    room.drop("spare", "TX-7")
    room.undo()
    room.drop("spare", "AZ-8")
    room.undo()
    assert room.get_parcels("spare") == []
    room.undo()  # SF-4 from the fixture
    assert room.get_parcels("west") == []
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    r = SortingRoom()
    with pytest.raises(SortingError):
        r.undo()
    r.add_bin("east")
    r.undo()
    with pytest.raises(SortingError):
        r.undo()
    assert r.get_bins() == []
    r.add_bin("east")
    r.drop("east", "NY-1")
    assert r.get_parcels("east") == ["NY-1"]


def test_the_whole_fixture_can_be_undone(room):
    for _ in range(7):
        room.undo()
    assert room.get_bins() == []
    with pytest.raises(SortingError):
        room.undo()


def test_several_picks_undone_come_back_in_order(room):
    room.pick("east")
    room.pick("east")
    room.pick("east")
    room.undo()
    room.undo()
    assert room.get_parcels("east") == ["LA-2", "NY-3"]
    room.undo()
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]
    assert [room.pick("east") for _ in range(3)] == ["NY-1", "LA-2", "NY-3"]
