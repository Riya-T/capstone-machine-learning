"""Hidden tests for the c_buffer change (adjustable gaps between bookings).
Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_buffer/private/test_buffer_new.py
"""

import pytest
from rooms import BookingError, RoomBusy, RoomPlanner

BAD_GAPS = [-1, -3]


def room_bookings(p, room):
    """The ids of the room's bookings, read through get_bookings()."""
    return [b for b in p.get_bookings() if p.get_booking(b)[0] == room]


@pytest.fixture
def planner():
    """hall needs 2 free slots, tidy 1, oak uses the default of 0."""
    p = RoomPlanner()
    p.add_room("hall", gap=2)
    p.add_room("tidy", gap=1)
    p.add_room("oak")
    for room in ("hall", "tidy", "oak"):
        p.book(f"{room}-1", room, 10)
    return p


def state(p):
    return {
        room: sorted((b, p.get_booking(b)) for b in room_bookings(p, room))
        for room in p.get_rooms()
    }


def test_buffer_default_is_still_zero(planner):
    assert planner.get_gap("oak") == 0
    with pytest.raises(RoomBusy):
        planner.book("x", "oak", 10)
    planner.book("x", "oak", 11)
    planner.book("y", "oak", 9)


def test_buffer_gaps_are_reported_per_room(planner):
    assert [planner.get_gap(r) for r in ("hall", "tidy", "oak")] == [2, 1, 0]


def test_buffer_room_gap_applies_to_booking(planner):
    before = state(planner)
    for slot in (8, 9, 10, 11, 12):
        with pytest.raises(RoomBusy):
            planner.book("x", "hall", slot)
    assert state(planner) == before
    planner.book("x", "hall", 13)
    planner.book("y", "hall", 7)
    assert sorted(room_bookings(planner, "hall")) == ["hall-1", "x", "y"]


def test_buffer_gap_of_one_keeps_the_neighbours_free(planner):
    for slot in (9, 10, 11):
        with pytest.raises(RoomBusy):
            planner.book("x", "tidy", slot)
    planner.book("x", "tidy", 12)
    planner.book("y", "tidy", 8)
    with pytest.raises(RoomBusy):
        planner.book("z", "tidy", 13)
    assert sorted(room_bookings(planner, "tidy")) == ["tidy-1", "x", "y"]


def test_buffer_room_gap_applies_to_free_rooms(planner):
    assert planner.get_free_rooms(10) == []
    assert planner.get_free_rooms(11) == ["oak"]
    assert planner.get_free_rooms(12) == ["tidy", "oak"]
    assert planner.get_free_rooms(13) == ["hall", "tidy", "oak"]
    assert planner.get_free_rooms(9) == ["oak"]
    assert planner.get_free_rooms(8) == ["tidy", "oak"]


def test_buffer_planner_gap_is_the_default_for_new_rooms():
    p = RoomPlanner(gap=1)
    p.add_room("a")
    p.add_room("b", gap=0)
    p.add_room("c", gap=None)
    assert [p.get_gap(r) for r in ("a", "b", "c")] == [1, 0, 1]
    p.book("x", "b", 0)
    p.book("y", "b", 1)
    p.book("z", "a", 0)
    with pytest.raises(RoomBusy):
        p.book("w", "a", 1)
    p.book("w", "a", 2)


def test_buffer_wide_planner_gap():
    p = RoomPlanner(gap=4)
    p.add_room("oak")
    p.book("a", "oak", 20)
    assert p.get_free_rooms(16) == []
    assert p.get_free_rooms(24) == []
    assert p.get_free_rooms(15) == ["oak"]
    assert p.get_free_rooms(25) == ["oak"]


def test_buffer_a_planner_gap_of_zero_is_the_default():
    p = RoomPlanner(gap=0)
    p.add_room("oak")
    assert p.get_gap("oak") == 0
    p.book("a", "oak", 3)
    p.book("b", "oak", 4)
    with pytest.raises(RoomBusy):
        p.book("c", "oak", 4)


@pytest.mark.parametrize("gap", BAD_GAPS)
def test_buffer_invalid_planner_gaps_are_rejected(gap):
    with pytest.raises(ValueError):
        RoomPlanner(gap=gap)


@pytest.mark.parametrize("gap", BAD_GAPS)
def test_buffer_invalid_room_gaps_add_no_room(gap):
    p = RoomPlanner()
    with pytest.raises(ValueError):
        p.add_room("oak", gap=gap)
    assert p.get_rooms() == []


def test_buffer_duplicate_room_is_still_refused(planner):
    with pytest.raises(BookingError):
        planner.add_room("hall", gap=5)
    assert planner.get_gap("hall") == 2


def test_buffer_gap_of_missing_room_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.get_gap("pine")
    with pytest.raises(KeyError):
        planner.get_gap(None)
