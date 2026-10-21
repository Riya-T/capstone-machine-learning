"""Hidden tests for the c_buffer change (adjustable gap between bookings).
Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_buffer/private/test_buffer_new.py
"""

import pytest
from rooms import BookingError, RoomBusy, RoomPlanner

BAD_GAPS = [-1, 2.5, "10", True]


@pytest.fixture
def planner():
    """hall needs 30 minutes, booth none, oak uses the default of 10."""
    p = RoomPlanner()
    p.add_room("hall", gap=30)
    p.add_room("booth", gap=0)
    p.add_room("oak")
    for room in ("hall", "booth", "oak"):
        p.book(f"{room}-1", room, 100, 160)
    return p


def state(p):
    return {
        room: [(b, p.get_booking(b)) for b in p.get_room_bookings(room)]
        for room in p.get_rooms()
    }


def test_buffer_default_is_still_ten(planner):
    assert planner.get_gap("oak") == 10
    with pytest.raises(RoomBusy):
        planner.book("x", "oak", 169, 200)
    planner.book("x", "oak", 170, 200)


def test_buffer_gaps_are_reported_per_room(planner):
    assert [planner.get_gap(r) for r in ("hall", "booth", "oak")] == [30, 0, 10]


def test_buffer_room_gap_applies_to_booking(planner):
    before = state(planner)
    with pytest.raises(RoomBusy):
        planner.book("x", "hall", 189, 220)
    with pytest.raises(RoomBusy):
        planner.book("x", "hall", 20, 71)
    assert state(planner) == before
    planner.book("x", "hall", 190, 220)
    planner.book("y", "hall", 20, 70)
    assert planner.get_room_bookings("hall") == ["y", "hall-1", "x"]


def test_buffer_zero_gap_allows_back_to_back_but_not_overlap(planner):
    planner.book("x", "booth", 160, 170)
    planner.book("y", "booth", 90, 100)
    with pytest.raises(RoomBusy):
        planner.book("z", "booth", 169, 180)
    with pytest.raises(RoomBusy):
        planner.book("z", "booth", 80, 91)
    assert planner.get_room_bookings("booth") == ["y", "booth-1", "x"]


def test_buffer_room_gap_applies_to_reschedule(planner):
    planner.book("x", "hall", 300, 330)
    with pytest.raises(RoomBusy):
        planner.reschedule("x", 180, 200)
    assert planner.get_booking("x") == ("hall", 300, 330)
    planner.reschedule("x", 190, 200)
    planner.book("y", "booth", 200, 210)
    planner.reschedule("y", 160, 170)
    assert planner.get_booking("y") == ("booth", 160, 170)


def test_buffer_room_gap_applies_to_free_rooms(planner):
    assert planner.get_free_rooms(160, 180) == ["booth"]
    assert planner.get_free_rooms(170, 180) == ["booth", "oak"]
    assert planner.get_free_rooms(190, 200) == ["hall", "booth", "oak"]


def test_buffer_planner_gap_is_the_default_for_new_rooms():
    p = RoomPlanner(gap=0)
    p.add_room("a")
    p.add_room("b", gap=5)
    p.add_room("c", gap=None)
    assert [p.get_gap(r) for r in ("a", "b", "c")] == [0, 5, 0]
    p.book("x", "a", 0, 10)
    p.book("y", "a", 10, 20)


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


def test_buffer_bad_gap_is_reported_before_a_duplicate_room(planner):
    with pytest.raises(ValueError):
        planner.add_room("hall", gap=-1)
    with pytest.raises(BookingError):
        planner.add_room("hall", gap=5)
    assert planner.get_gap("hall") == 30


def test_buffer_gap_of_missing_room_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.get_gap("pine")
    with pytest.raises(KeyError):
        planner.get_gap(None)
