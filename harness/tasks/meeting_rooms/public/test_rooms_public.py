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
    planner.book("standup", "oak", 540, 555)
    assert planner.get_booking("standup") == ("oak", 540, 555)
    assert planner.get_room_bookings("oak") == ["standup"]
    assert planner.get_room_bookings("elm") == []


def test_the_gap_between_bookings_is_ten_minutes(planner):
    planner.book("a", "oak", 60, 120)
    planner.book("b", "oak", 130, 150)
    with pytest.raises(RoomBusy):
        planner.book("c", "oak", 155, 200)
    assert planner.get_room_bookings("oak") == ["a", "b"]


def test_room_bookings_are_listed_earliest_first(planner):
    planner.book("late", "oak", 600, 660)
    planner.book("early", "oak", 300, 360)
    assert planner.get_room_bookings("oak") == ["early", "late"]


def test_a_booking_can_be_moved_over_its_own_old_times(planner):
    planner.book("a", "oak", 100, 160)
    planner.reschedule("a", 130, 190)
    assert planner.get_booking("a") == ("oak", 130, 190)


def test_free_rooms_skip_rooms_with_an_overlapping_booking(planner):
    planner.book("a", "oak", 100, 200)
    assert planner.get_free_rooms(150, 180) == ["elm"]
    assert planner.get_free_rooms(400, 460) == ["oak", "elm"]


def test_unknown_room_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.book("a", "pine", 0, 30)
