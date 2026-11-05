"""Public checks for the c_versions change (versioned bookings). Shown to the
editor, never to the writer.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/public/test_versions_public.py
"""

import pytest
from seats import NotEnoughSeats, SeatPlanner, VersionConflict


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # limit 7
    p.add_coach("B", 20)  # limit 14
    p.reserve("smith", 2)
    return p


def test_versions_start_at_one_and_count_moves(planner):
    assert planner.get_version("smith") == 1
    planner.move("smith", "B", expected_version=1)
    assert planner.get_version("smith") == 2


def test_versions_a_stale_move_is_refused(planner):
    planner.move("smith", "B")
    with pytest.raises(VersionConflict):
        planner.move("smith", "A", expected_version=1)
    assert planner.get_booking("smith") == ("B", 2)
    assert planner.get_version("smith") == 2


def test_versions_add_seats_to_a_booking(planner):
    planner.add_seats("smith", 2)
    assert planner.get_booking("smith") == ("A", 4)
    assert planner.get_reserved("A") == 4
    assert planner.get_version("smith") == 2


def test_versions_add_seats_needs_room_left_in_the_coach(planner):
    planner.reserve("jones", 4)  # A: 6 of 7 reserved, room for 1 more
    with pytest.raises(NotEnoughSeats):
        planner.add_seats("smith", 2)
    assert planner.get_booking("smith") == ("A", 2)
    planner.add_seats("smith", 1)
    assert planner.get_booking("smith") == ("A", 3)
    assert planner.get_available("A") == 0
