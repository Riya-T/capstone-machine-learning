"""Public checks for seats.py.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest public/test_seats_public.py
"""

import pytest
from seats import NotEnoughSeats, SeatPlanner


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # limit 7
    p.add_coach("B", 20)  # limit 14
    return p


def test_a_group_gets_the_first_seats_of_the_first_coach(planner):
    assert planner.reserve("smith", 3) == "A"
    assert planner.get_booking("smith") == ("A", [1, 2, 3])
    assert planner.get_reserved("A") == 3
    assert planner.get_available("A") == 4


def test_a_coach_is_never_filled_beyond_seventy_percent(planner):
    assert planner.reserve("smith", 7) == "A"
    assert planner.get_available("A") == 0
    assert planner.reserve("jones", 1) == "B"
    assert planner.get_booking("jones") == ("B", [1])


def test_a_group_too_big_for_any_coach_raises(planner):
    with pytest.raises(NotEnoughSeats):
        planner.reserve("school", 15)
    assert planner.get_reserved("A") == 0
    assert planner.get_reserved("B") == 0


def test_seats_freed_by_a_move_are_used_again(planner):
    planner.reserve("smith", 2)
    planner.reserve("jones", 3)
    planner.move("smith", "B")
    assert planner.get_booking("smith") == ("B", [1, 2])
    assert planner.reserve("brown", 3) == "A"
    assert planner.get_booking("brown") == ("A", [1, 2, 6])


def test_group_sizes_must_be_positive(planner):
    with pytest.raises(ValueError):
        planner.reserve("smith", 0)
    with pytest.raises(ValueError):
        planner.reserve("smith", -2)


def test_unknown_ids_raise_key_error(planner):
    with pytest.raises(KeyError):
        planner.get_booking("nobody")
    with pytest.raises(KeyError):
        planner.get_available("Z")
