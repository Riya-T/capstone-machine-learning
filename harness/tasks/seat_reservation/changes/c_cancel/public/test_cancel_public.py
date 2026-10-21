"""Public checks for the c_cancel change (cancellations). Shown to the
editor, never to the writer.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/public/test_cancel_public.py
"""

import pytest
from seats import SeatPlanner


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # limit 7
    p.add_coach("B", 20)  # limit 14
    return p


def test_cancelling_a_whole_booking(planner):
    planner.reserve("smith", 3)
    planner.cancel("smith")
    assert planner.get_reserved("A") == 0
    assert planner.get_cancelled() == ["smith"]
    with pytest.raises(KeyError):
        planner.get_booking("smith")


def test_cancelling_part_of_a_booking_frees_its_highest_seats(planner):
    planner.reserve("smith", 4)
    planner.cancel("smith", 1)
    assert planner.get_booking("smith") == ("A", [1, 2, 3])
    assert planner.get_reserved("A") == 3
    assert planner.get_cancelled() == []


def test_cancelled_seats_are_booked_again(planner):
    planner.reserve("smith", 2)
    planner.reserve("jones", 2)
    planner.cancel("smith")
    assert planner.reserve("brown", 3) == "A"
    assert planner.get_booking("brown") == ("A", [1, 2, 5])
