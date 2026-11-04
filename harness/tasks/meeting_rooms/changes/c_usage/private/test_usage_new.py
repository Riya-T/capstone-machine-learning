"""Hidden tests for the c_usage change (booked slots and usage ranking).
Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_usage/private/test_usage_new.py
"""

import pytest
from rooms import RoomPlanner

BAD_STRETCHES = [(-1, 5), (5, 5), (6, 5)]


@pytest.fixture
def planner():
    """oak: slots 10, 11 and 20; elm: slot 0; ash: nothing."""
    p = RoomPlanner()
    for room in ("oak", "elm", "ash"):
        p.add_room(room)
    p.book("a", "oak", 10)
    p.book("b", "oak", 11)
    p.book("e", "oak", 20)
    p.book("c", "elm", 0)
    return p


@pytest.mark.parametrize(
    "first,last,slots",
    [
        (0, 100, 3),
        (10, 11, 1),
        (10, 12, 2),
        (11, 12, 1),
        (12, 20, 0),
        (12, 21, 1),
        (0, 10, 0),
        (20, 21, 1),
        (11, 13, 1),
        (9, 10, 0),
    ],
)
def test_usage_counts_bookings_in_the_stretch(planner, first, last, slots):
    assert planner.get_booked_slots("oak", first, last) == slots


def test_usage_rooms_without_bookings_give_zero(planner):
    assert planner.get_booked_slots("ash", 0, 1000) == 0
    assert planner.get_booked_slots("elm", 1, 1000) == 0
    assert planner.get_booked_slots("elm", 0, 1) == 1


def test_usage_follows_new_bookings(planner):
    planner.book("d", "elm", 5)
    planner.book("f", "elm", 1)
    assert planner.get_booked_slots("elm", 0, 10) == 3
    assert planner.get_booked_slots("elm", 1, 10) == 2


def test_usage_ranking_orders_by_slots(planner):
    assert planner.get_usage_ranking(0, 1000) == [("oak", 3), ("elm", 1), ("ash", 0)]


def test_usage_ranking_ties_keep_the_order_rooms_were_added(planner):
    planner.book("d", "ash", 0)
    assert planner.get_usage_ranking(0, 1000) == [("oak", 3), ("elm", 1), ("ash", 1)]
    assert planner.get_usage_ranking(50, 60) == [("oak", 0), ("elm", 0), ("ash", 0)]


def test_usage_ranking_uses_the_stretch(planner):
    for booking_id, slot in [("d", 2), ("f", 3), ("g", 4)]:
        planner.book(booking_id, "ash", slot)
    assert planner.get_usage_ranking(0, 8) == [("ash", 3), ("elm", 1), ("oak", 0)]
    assert planner.get_usage_ranking(1, 12) == [("ash", 3), ("oak", 2), ("elm", 0)]


def test_usage_ranking_with_no_rooms_is_empty():
    assert RoomPlanner().get_usage_ranking(0, 10) == []


@pytest.mark.parametrize("first,last", BAD_STRETCHES)
def test_usage_invalid_stretches_raise_value_error(planner, first, last):
    with pytest.raises(ValueError):
        planner.get_booked_slots("oak", first, last)
    with pytest.raises(ValueError):
        planner.get_usage_ranking(first, last)


def test_usage_missing_room_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.get_booked_slots("pine", 0, 10)
    with pytest.raises(KeyError):
        planner.get_booked_slots(None, 0, 10)


def test_usage_queries_change_nothing(planner):
    planner.get_booked_slots("oak", 0, 1000)
    planner.get_usage_ranking(0, 1000)
    assert sorted(planner.get_bookings()) == ["a", "b", "c", "e"]
    assert planner.get_booking("a") == ("oak", 10)
