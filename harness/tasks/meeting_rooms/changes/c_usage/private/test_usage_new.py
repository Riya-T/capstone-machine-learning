"""Hidden tests for the c_usage change (booked minutes and room ranking).
Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_usage/private/test_usage_new.py
"""

import pytest
from rooms import RoomPlanner

BAD_WINDOWS = [(-1, 30), (30, 30), (40, 30), (0, 2.5), ("0", 30), (0, None)]


@pytest.fixture
def planner():
    """oak: 100-160 and 200-260; elm: 0-30; ash: nothing."""
    p = RoomPlanner()
    for room in ("oak", "elm", "ash"):
        p.add_room(room)
    p.book("a", "oak", 100, 160)
    p.book("b", "oak", 200, 260)
    p.book("c", "elm", 0, 30)
    return p


@pytest.mark.parametrize(
    "start,end,minutes",
    [
        (0, 1000, 120),
        (100, 160, 60),
        (90, 110, 10),
        (150, 210, 20),
        (160, 200, 0),
        (120, 130, 10),
        (259, 300, 1),
        (0, 100, 0),
    ],
)
def test_usage_clips_bookings_to_the_window(planner, start, end, minutes):
    assert planner.get_booked_minutes("oak", start, end) == minutes


def test_usage_rooms_without_bookings_give_zero(planner):
    assert planner.get_booked_minutes("ash", 0, 1000) == 0


def test_usage_follows_reschedules(planner):
    planner.reschedule("c", 500, 600)
    assert planner.get_booked_minutes("elm", 0, 100) == 0
    assert planner.get_booked_minutes("elm", 0, 1000) == 100


def test_usage_ranking_orders_by_minutes(planner):
    assert planner.get_usage_ranking(0, 1000) == [("oak", 120), ("elm", 30), ("ash", 0)]


def test_usage_ranking_ties_keep_the_order_rooms_were_added(planner):
    planner.book("d", "ash", 0, 30)
    assert planner.get_usage_ranking(0, 1000) == [("oak", 120), ("elm", 30), ("ash", 30)]
    assert planner.get_usage_ranking(500, 600) == [("oak", 0), ("elm", 0), ("ash", 0)]


def test_usage_ranking_uses_the_window(planner):
    planner.book("d", "ash", 0, 90)
    assert planner.get_usage_ranking(0, 100) == [("ash", 90), ("elm", 30), ("oak", 0)]
    assert planner.get_usage_ranking(20, 120) == [("ash", 70), ("oak", 20), ("elm", 10)]


def test_usage_ranking_with_no_rooms_is_empty():
    assert RoomPlanner().get_usage_ranking(0, 10) == []


@pytest.mark.parametrize("start,end", BAD_WINDOWS)
def test_usage_invalid_windows_raise_value_error(planner, start, end):
    with pytest.raises(ValueError):
        planner.get_booked_minutes("oak", start, end)
    with pytest.raises(ValueError):
        planner.get_usage_ranking(start, end)


def test_usage_missing_room_raises_key_error_first(planner):
    with pytest.raises(KeyError):
        planner.get_booked_minutes("pine", 0, 10)
    with pytest.raises(KeyError):
        planner.get_booked_minutes("pine", -5, -10)
    with pytest.raises(KeyError):
        planner.get_booked_minutes(None, 0, 10)


def test_usage_queries_change_nothing(planner):
    planner.get_booked_minutes("oak", 0, 1000)
    planner.get_usage_ranking(0, 1000)
    assert planner.get_room_bookings("oak") == ["a", "b"]
    assert planner.get_booking("a") == ("oak", 100, 160)
