"""Public checks for rooms.py.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest public/test_rooms_public.py
"""

import pytest
from rooms import RoomBusy, RoomPlanner


@pytest.fixture
def planner():
    p = RoomPlanner()
    p.add_room("oak")
    p.add_room("elm")
    return p


def test_a_booking_can_be_read_back(planner):
    planner.book("standup", "oak", 9)
    assert planner.get_booking("standup") == ("oak", 9)
    assert planner.get_bookings() == ["standup"]


def test_the_same_slot_cannot_be_booked_twice(planner):
    planner.book("a", "oak", 5)
    with pytest.raises(RoomBusy):
        planner.book("b", "oak", 5)
    planner.book("b", "elm", 5)
    assert sorted(planner.get_bookings()) == ["a", "b"]
    assert planner.get_booking("b") == ("elm", 5)


def test_back_to_back_bookings_are_allowed(planner):
    planner.book("a", "oak", 5)
    planner.book("b", "oak", 6)
    planner.book("c", "oak", 4)
    assert sorted(planner.get_bookings()) == ["a", "b", "c"]
    assert planner.get_booking("c") == ("oak", 4)


def test_free_rooms_skip_rooms_with_a_booking_in_that_slot(planner):
    planner.book("a", "oak", 12)
    assert planner.get_free_rooms(12) == ["elm"]
    assert planner.get_free_rooms(13) == ["oak", "elm"]
    assert planner.get_free_rooms(11) == ["oak", "elm"]


def test_free_rooms_check_the_slot_like_book(planner):
    with pytest.raises(ValueError):
        planner.get_free_rooms(-1)
    with pytest.raises(ValueError):
        planner.book("a", "oak", -1)


def test_unknown_room_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.book("a", "pine", 0)
