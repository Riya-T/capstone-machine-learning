"""Hidden tests for the initial mail_bins spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with sorting.py importable, e.g. in the sandbox):
    python -m pytest private/test_sorting_initial.py
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
    return r


def state(r):
    """Every bin in order with a copy of its parcels, to check that a failed
    call changed nothing."""
    return [(b, list(r.get_parcels(b))) for b in list(r.get_bins())]


# --- bins ---------------------------------------------------------------------


def test_a_new_bin_is_empty():
    r = SortingRoom()
    r.add_bin("east")
    assert r.get_parcels("east") == []
    assert r.get_bins() == ["east"]


def test_bins_are_listed_in_the_order_added():
    r = SortingRoom()
    for name in ["west", "north", "east"]:
        r.add_bin(name)
    assert r.get_bins() == ["west", "north", "east"]


def test_adding_a_name_in_use_is_rejected(room):
    before = state(room)
    with pytest.raises(SortingError):
        room.add_bin("west")
    assert state(room) == before


def test_a_closed_name_can_be_added_again_as_a_new_empty_bin(room):
    room.close_bin("east", "spare")
    room.add_bin("east")
    assert room.get_bins() == ["west", "spare", "east"]
    assert room.get_parcels("east") == []
    assert room.get_parcels("spare") == ["NY-1", "LA-2", "NY-3"]


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.drop("north", "TX-9"),
        lambda r: r.pick("north"),
        lambda r: r.empty_bin_into("north", "west"),
        lambda r: r.empty_bin_into("east", "north"),
        lambda r: r.close_bin("north", "west"),
        lambda r: r.close_bin("east", "north"),
        lambda r: r.get_parcels("north"),
    ],
)
def test_bins_never_added_raise_key_error(room, call):
    before = state(room)
    with pytest.raises(KeyError):
        call(room)
    assert state(room) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.drop("spare", "AZ-9"),
        lambda r: r.pick("spare"),
        lambda r: r.empty_bin_into("spare", "west"),
        lambda r: r.empty_bin_into("east", "spare"),
        lambda r: r.close_bin("spare", "west"),
        lambda r: r.close_bin("east", "spare"),
        lambda r: r.get_parcels("spare"),
    ],
)
def test_a_closed_bin_is_not_in_use(room, call):
    room.drop("spare", "TX-9")
    room.close_bin("spare", "west")
    before = state(room)
    with pytest.raises(KeyError):
        call(room)
    assert state(room) == before


# --- drop and pick ------------------------------------------------------------


def test_parcels_are_listed_in_arrival_order(room):
    for parcel in ["TX-7", "AZ-5", "NY-8"]:
        room.drop("spare", parcel)
    assert room.get_parcels("spare") == ["TX-7", "AZ-5", "NY-8"]


def test_a_parcel_in_any_bin_cannot_be_dropped_again(room):
    before = state(room)
    with pytest.raises(SortingError):
        room.drop("east", "NY-3")
    with pytest.raises(SortingError):
        room.drop("spare", "LA-2")
    with pytest.raises(SortingError):
        room.drop("east", "SF-4")
    assert state(room) == before


def test_pick_takes_parcels_from_the_front_in_arrival_order(room):
    room.drop("east", "TX-7")
    assert [room.pick("east") for _ in range(4)] == ["NY-1", "LA-2", "NY-3", "TX-7"]
    assert room.get_parcels("east") == []
    assert room.get_parcels("west") == ["SF-4"]


def test_picking_from_an_empty_bin_is_rejected(room):
    before = state(room)
    with pytest.raises(SortingError):
        room.pick("spare")
    assert state(room) == before
    room.pick("west")
    with pytest.raises(SortingError):
        room.pick("west")


def test_a_picked_parcel_can_be_dropped_again_at_the_back(room):
    assert room.pick("east") == "NY-1"
    room.drop("east", "NY-1")
    assert room.get_parcels("east") == ["LA-2", "NY-3", "NY-1"]


# --- recall -------------------------------------------------------------------


def test_recall_returns_the_bin_and_keeps_the_others_in_order(room):
    assert room.recall("NY-1") == "east"
    assert room.get_parcels("east") == ["LA-2", "NY-3"]
    assert room.recall("SF-4") == "west"
    assert room.get_parcels("west") == []


def test_recalling_a_parcel_in_no_bin_is_rejected(room):
    before = state(room)
    with pytest.raises(SortingError):
        room.recall("TX-9")
    room.pick("east")
    with pytest.raises(SortingError):
        room.recall("NY-1")
    assert room.get_parcels("east") == ["LA-2", "NY-3"]


def test_a_recalled_parcel_can_be_dropped_into_another_bin(room):
    room.recall("LA-2")
    room.drop("spare", "LA-2")
    assert room.get_parcels("spare") == ["LA-2"]
    assert room.get_parcels("east") == ["NY-1", "NY-3"]


# --- empty_bin_into and close_bin -----------------------------------------


def test_empty_bin_into_keeps_the_order_behind_the_parcels_there(room):
    assert room.empty_bin_into("east", "west") == 3
    assert room.get_parcels("west") == ["SF-4", "NY-1", "LA-2", "NY-3"]
    assert room.get_parcels("east") == []
    assert room.get_bins() == ["east", "west", "spare"]


def test_a_bin_emptied_into_another_can_be_used_again(room):
    room.empty_bin_into("east", "spare")
    room.drop("east", "TX-7")
    assert room.get_parcels("east") == ["TX-7"]
    assert room.pick("spare") == "NY-1"


def test_empty_bin_into_from_an_empty_bin_moves_nothing(room):
    before = state(room)
    assert room.empty_bin_into("spare", "east") == 0
    assert state(room) == before


def test_close_bin_moves_every_parcel_and_closes_it(room):
    assert room.close_bin("east", "west") == 3
    assert room.get_bins() == ["west", "spare"]
    assert room.get_parcels("west") == ["SF-4", "NY-1", "LA-2", "NY-3"]


def test_closing_an_empty_bin_moves_nothing(room):
    assert room.close_bin("spare", "east") == 0
    assert room.get_bins() == ["east", "west"]
    assert room.get_parcels("east") == ["NY-1", "LA-2", "NY-3"]


def test_the_other_bins_keep_their_order_after_a_close(room):
    room.add_bin("north")
    room.close_bin("west", "north")
    assert room.get_bins() == ["east", "spare", "north"]


def test_moved_parcels_are_still_in_the_room(room):
    room.close_bin("east", "spare")
    with pytest.raises(SortingError):
        room.drop("west", "LA-2")
    assert room.recall("LA-2") == "spare"


@pytest.mark.parametrize(
    "call",
    [
        lambda r: r.empty_bin_into("east", "east"),
        lambda r: r.close_bin("east", "east"),
        lambda r: r.empty_bin_into("spare", "spare"),
    ],
    ids=["empty_bin_into", "close_bin", "empty_bin_into_empty"],
)
def test_the_same_bin_on_both_sides_is_rejected(room, call):
    before = state(room)
    with pytest.raises(ValueError):
        call(room)
    assert state(room) == before


# --- general ----------------------------------------------------------------


def test_rooms_do_not_share_bins():
    first, second = SortingRoom(), SortingRoom()
    first.add_bin("east")
    first.drop("east", "NY-1")
    assert second.get_bins() == []
    second.add_bin("east")
    second.drop("east", "NY-1")
    assert second.get_parcels("east") == ["NY-1"]
