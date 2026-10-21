"""Hidden tests for the c_booking_versions change (booking versions and
conflict detection). Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_booking_versions/private/test_booking_versions_new.py
"""

import pytest
from rooms import BookingError, RoomBusy, RoomPlanner, VersionConflict


@pytest.fixture
def planner():
    p = RoomPlanner()
    p.add_room("oak")
    p.add_room("elm")
    p.book("a", "oak", 100, 160)
    p.book("b", "oak", 300, 360)
    p.book("c", "elm", 100, 160)
    return p


def state(p):
    return {
        room: [(b, p.get_booking(b), p.get_version(b)) for b in p.get_room_bookings(room)]
        for room in p.get_rooms()
    }


def test_versioned_new_bookings_start_at_one(planner):
    assert [planner.get_version(b) for b in ("a", "b", "c")] == [1, 1, 1]


def test_versioned_each_booking_counts_its_own_moves(planner):
    planner.reschedule("a", 120, 180)
    planner.reschedule("a", 130, 190)
    planner.reschedule("c", 0, 30)
    assert [planner.get_version(b) for b in ("a", "b", "c")] == [3, 1, 2]


def test_versioned_a_move_to_the_same_times_still_counts(planner):
    planner.reschedule("a", 100, 160)
    assert planner.get_version("a") == 2
    assert planner.get_booking("a") == ("oak", 100, 160)


def test_versioned_matching_expected_versions_are_accepted(planner):
    planner.reschedule("a", 120, 180, expected_version=1)
    planner.reschedule("a", 0, 60, expected_version=2)
    assert planner.get_booking("a") == ("oak", 0, 60)
    assert planner.get_version("a") == 3


@pytest.mark.parametrize("expected", [0, 2, 10])
def test_versioned_a_mismatch_changes_nothing(planner, expected):
    before = state(planner)
    with pytest.raises(VersionConflict):
        planner.reschedule("a", 500, 560, expected_version=expected)
    assert state(planner) == before


def test_versioned_none_means_no_check(planner):
    planner.reschedule("a", 120, 180)
    planner.reschedule("a", 0, 60, expected_version=None)
    assert planner.get_version("a") == 3


def test_versioned_failed_moves_do_not_count(planner):
    with pytest.raises(RoomBusy):
        planner.reschedule("a", 280, 300)
    with pytest.raises(ValueError):
        planner.reschedule("a", 50, 40)
    with pytest.raises(VersionConflict):
        planner.reschedule("a", 0, 30, expected_version=4)
    assert planner.get_version("a") == 1
    assert planner.get_booking("a") == ("oak", 100, 160)


def test_versioned_conflict_class(planner):
    assert issubclass(VersionConflict, BookingError)
    assert not issubclass(VersionConflict, RoomBusy)


def test_versioned_missing_booking_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.get_version("zz")
    with pytest.raises(KeyError):
        planner.get_version(None)
    with pytest.raises(KeyError):
        planner.reschedule("zz", 0, 30, expected_version=1)


def test_versioned_bad_times_are_reported_before_a_conflict(planner):
    with pytest.raises(ValueError):
        planner.reschedule("a", -1, 30, expected_version=7)


def test_versioned_conflict_is_reported_before_a_busy_room(planner):
    with pytest.raises(VersionConflict):
        planner.reschedule("a", 300, 360, expected_version=7)
    with pytest.raises(RoomBusy):
        planner.reschedule("a", 300, 360, expected_version=1)


def test_versioned_new_booking_with_a_fresh_id_starts_again_at_one(planner):
    planner.reschedule("c", 0, 30)
    planner.book("d", "elm", 100, 160)
    assert planner.get_version("d") == 1
    assert planner.get_version("c") == 2
