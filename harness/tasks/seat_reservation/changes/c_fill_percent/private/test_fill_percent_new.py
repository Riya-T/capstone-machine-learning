"""Hidden tests for the c_fill_percent change (adjustable fill rule). Never
shown to the writer or the editor.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest changes/c_fill_percent/private/test_fill_percent_new.py
"""

import pytest
from seats import NotEnoughSeats, ReservationError, SeatPlanner

BAD_PERCENTS = [0, 101, -5, 50.0, "70", True, None]


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # limit 7
    p.add_coach("B", 20)  # limit 14
    return p


def state(p, bookings=()):
    coaches = {
        c: (p.get_reserved(c), p.get_available(c), p.get_fill_percent(c)) for c in p.get_coaches()
    }
    return coaches, {b: p.get_booking(b) for b in bookings}


def test_fill_percent_defaults_to_seventy(planner):
    assert planner.get_fill_percent("A") == 70
    assert planner.get_available("A") == 7


@pytest.mark.parametrize(
    "seats, percent, limit", [(10, 100, 10), (10, 25, 2), (15, 50, 7), (3, 1, 0), (7, 99, 6)]
)
def test_fill_percent_limit_is_rounded_down(seats, percent, limit):
    p = SeatPlanner()
    p.add_coach("X", seats, fill_percent=percent)
    assert p.get_available("X") == limit


def test_fill_percent_of_the_planner_is_used_by_every_coach_without_one():
    p = SeatPlanner(fill_percent=40)
    p.add_coach("A", 10)
    p.add_coach("B", 10, fill_percent=90)
    p.add_coach("C", 5)
    assert [p.get_fill_percent(c) for c in ["A", "B", "C"]] == [40, 90, 40]
    assert [p.get_available(c) for c in ["A", "B", "C"]] == [4, 9, 2]


@pytest.mark.parametrize("percent", BAD_PERCENTS)
def test_fill_percent_invalid_for_the_planner(percent):
    with pytest.raises(ValueError):
        SeatPlanner(fill_percent=percent)


@pytest.mark.parametrize("percent", [p for p in BAD_PERCENTS if p is not None])
def test_fill_percent_invalid_for_a_coach(planner, percent):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.add_coach("C", 10, fill_percent=percent)
    assert state(planner) == before
    assert planner.get_coaches() == ["A", "B"]


def test_fill_percent_bad_value_is_reported_before_a_repeated_coach(planner):
    with pytest.raises(ValueError):
        planner.add_coach("A", 10, fill_percent=0)


def test_fill_percent_is_used_by_reserve_and_move():
    p = SeatPlanner()
    p.add_coach("A", 10, fill_percent=100)
    p.add_coach("B", 10, fill_percent=30)
    assert p.reserve("smith", 10) == "A"
    assert p.reserve("jones", 3) == "B"
    with pytest.raises(NotEnoughSeats):
        p.reserve("brown", 1)
    p.add_coach("C", 10, fill_percent=20)
    with pytest.raises(NotEnoughSeats):
        p.move("jones", "C")
    assert p.get_booking("jones") == ("B", [1, 2, 3])


def test_fill_percent_can_be_raised_later(planner):
    planner.reserve("smith", 7)
    planner.set_fill_percent("A", 90)
    assert planner.get_fill_percent("A") == 90
    assert planner.get_available("A") == 2
    assert planner.reserve("jones", 2) == "A"
    assert planner.get_booking("jones") == ("A", [8, 9])
    assert planner.get_fill_percent("B") == 70


def test_fill_percent_can_be_lowered_to_exactly_the_reserved_seats(planner):
    planner.reserve("smith", 5)
    planner.set_fill_percent("A", 50)
    assert planner.get_available("A") == 0
    before = state(planner, ["smith"])
    with pytest.raises(ReservationError):
        planner.set_fill_percent("A", 40)
    assert state(planner, ["smith"]) == before
    assert planner.get_fill_percent("A") == 50


@pytest.mark.parametrize("percent", BAD_PERCENTS)
def test_fill_percent_invalid_when_setting(planner, percent):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.set_fill_percent("A", percent)
    assert state(planner) == before


def test_fill_percent_errors_come_in_order(planner):
    planner.reserve("smith", 7)
    with pytest.raises(KeyError):
        planner.set_fill_percent("Z", 0)
    with pytest.raises(ValueError):
        planner.set_fill_percent("A", 0)  # bad value before the reserved-seat check
    with pytest.raises(KeyError):
        planner.get_fill_percent("Z")
    with pytest.raises(KeyError):
        planner.get_fill_percent(None)
