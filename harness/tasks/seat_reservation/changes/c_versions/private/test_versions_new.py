"""Hidden tests for the c_versions change (versioned bookings). Never shown
to the writer or the editor.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/private/test_versions_new.py
"""

import pytest
from seats import NotEnoughSeats, ReservationError, SeatPlanner, VersionConflict


@pytest.fixture
def planner():
    p = SeatPlanner()
    p.add_coach("A", 10)  # limit 7
    p.add_coach("B", 20)  # limit 14
    p.reserve("smith", 2)  # A 1-2
    p.reserve("jones", 2)  # A 3-4
    return p


def state(p, bookings=("smith", "jones")):
    coaches = {c: (p.get_reserved(c), p.get_available(c)) for c in p.get_coaches()}
    return coaches, {b: (p.get_booking(b), p.get_version(b)) for b in bookings}


def test_versions_conflict_is_a_reservation_error():
    assert issubclass(VersionConflict, ReservationError)


def test_versions_only_change_for_the_booking_that_changed(planner):
    planner.move("smith", "B")
    planner.add_seats("smith", 1)
    planner.move("smith", "A")
    assert planner.get_version("smith") == 4
    assert planner.get_version("jones") == 1


def test_versions_with_the_right_expected_version_succeed(planner):
    planner.move("smith", "B", expected_version=1)
    planner.add_seats("smith", 3, expected_version=2)
    planner.move("smith", "A", expected_version=3)
    assert planner.get_booking("smith") == ("A", [1, 2, 5, 6, 7])
    assert planner.get_version("smith") == 4


def test_versions_none_means_no_check(planner):
    planner.move("smith", "B", expected_version=None)
    planner.add_seats("smith", 1, expected_version=None)
    assert planner.get_version("smith") == 3


@pytest.mark.parametrize("stale", [0, 2, 5, "1"])
def test_versions_a_stale_add_seats_is_refused(planner, stale):
    before = state(planner)
    with pytest.raises(VersionConflict):
        planner.add_seats("smith", 1, expected_version=stale)
    assert state(planner) == before


def test_versions_a_failed_move_keeps_the_version(planner):
    planner.reserve("brown", 14)  # fills B
    before = state(planner, ["smith", "jones", "brown"])
    with pytest.raises(NotEnoughSeats):
        planner.move("smith", "B", expected_version=1)
    with pytest.raises(ValueError):
        planner.move("smith", "A")
    assert state(planner, ["smith", "jones", "brown"]) == before


def test_versions_add_seats_takes_the_lowest_free_seats(planner):
    planner.reserve("brown", 2)  # A 5-6
    planner.move("jones", "B")  # frees A 3-4
    planner.add_seats("smith", 3)  # A has room for 3: seats 3, 4 and 7
    assert planner.get_booking("smith") == ("A", [1, 2, 3, 4, 7])
    assert planner.get_available("A") == 0


def test_versions_add_seats_past_the_limit_raises(planner):
    before = state(planner)
    with pytest.raises(NotEnoughSeats):
        planner.add_seats("smith", 4)  # A has 3 left
    assert state(planner) == before
    planner.add_seats("smith", 3)
    assert planner.get_available("A") == 0


@pytest.mark.parametrize("count", [0, -1, 1.5, "2", True])
def test_versions_add_seats_with_a_bad_count_is_rejected(planner, count):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.add_seats("smith", count)
    assert state(planner) == before


def test_versions_unknown_bookings_raise_key_error(planner):
    with pytest.raises(KeyError):
        planner.get_version("nobody")
    with pytest.raises(KeyError):
        planner.get_version(None)
    with pytest.raises(KeyError):
        planner.add_seats("nobody", 0, expected_version=99)


def test_versions_move_errors_come_in_order(planner):
    planner.reserve("brown", 14)  # fills B
    with pytest.raises(ValueError):
        planner.move("smith", "A", expected_version=99)  # same coach first
    with pytest.raises(VersionConflict):
        planner.move("smith", "B", expected_version=99)  # conflict before no room


def test_versions_add_seats_errors_come_in_order(planner):
    with pytest.raises(ValueError):
        planner.add_seats("smith", 0, expected_version=99)  # bad count first
    with pytest.raises(VersionConflict):
        planner.add_seats("smith", 50, expected_version=99)  # conflict before no room
