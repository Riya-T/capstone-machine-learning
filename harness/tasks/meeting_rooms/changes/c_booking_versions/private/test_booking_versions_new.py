"""Hidden tests for the c_booking_versions change (moving bookings, with
versions). Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_booking_versions/private/test_booking_versions_new.py
"""

import pytest
from rooms import BookingError, RoomBusy, RoomPlanner, VersionConflict


def room_bookings(p, room):
    """The ids of the room's bookings, read through get_bookings()."""
    return [b for b in p.get_bookings() if p.get_booking(b)[0] == room]


@pytest.fixture
def planner():
    """oak keeps one free slot between meetings, elm none."""
    p = RoomPlanner()
    p.add_room("oak", gap=1)
    p.add_room("elm")
    p.book("a", "oak", 10)
    p.book("b", "oak", 30)
    p.book("c", "elm", 10)
    return p


def state(p):
    return {
        room: sorted((b, p.get_booking(b), p.get_version(b)) for b in room_bookings(p, room))
        for room in p.get_rooms()
    }


def test_versioned_new_bookings_start_at_one(planner):
    assert [planner.get_version(b) for b in ("a", "b", "c")] == [1, 1, 1]


def test_versioned_each_booking_counts_its_own_moves(planner):
    planner.reschedule("a", 12)
    planner.reschedule("a", 13)
    planner.reschedule("c", 0)
    assert [planner.get_version(b) for b in ("a", "b", "c")] == [3, 1, 2]
    assert planner.get_booking("a") == ("oak", 13)
    assert planner.get_booking("c") == ("elm", 0)


def test_versioned_a_move_to_the_same_slot_still_counts(planner):
    planner.reschedule("a", 10)
    planner.reschedule("c", 10)
    assert planner.get_version("a") == 2
    assert planner.get_version("c") == 2
    assert planner.get_booking("a") == ("oak", 10)


def test_versioned_a_move_may_overlap_its_own_old_slot(planner):
    planner.reschedule("a", 11)
    planner.reschedule("a", 10)
    planner.reschedule("a", 9)
    assert planner.get_booking("a") == ("oak", 9)
    assert planner.get_version("a") == 4


@pytest.mark.parametrize("slot", [29, 30, 31])
def test_versioned_moves_are_checked_against_the_other_bookings(planner, slot):
    before = state(planner)
    with pytest.raises(RoomBusy):
        planner.reschedule("a", slot)
    assert state(planner) == before


def test_versioned_moves_stay_in_their_room(planner):
    planner.reschedule("a", 28)
    planner.reschedule("c", 30)
    assert planner.get_booking("a") == ("oak", 28)
    assert sorted(room_bookings(planner, "oak")) == ["a", "b"]
    assert room_bookings(planner, "elm") == ["c"]


def test_versioned_a_move_frees_the_old_slot(planner):
    planner.reschedule("a", 20)
    assert planner.get_free_rooms(10) == ["oak"]
    planner.book("d", "oak", 11)
    planner.reschedule("c", 11)
    planner.book("e", "elm", 10)
    assert sorted(planner.get_bookings()) == ["a", "b", "c", "d", "e"]


def test_versioned_matching_expected_versions_are_accepted(planner):
    planner.reschedule("a", 12, expected_version=1)
    planner.reschedule("a", 0, expected_version=2)
    assert planner.get_booking("a") == ("oak", 0)
    assert planner.get_version("a") == 3


@pytest.mark.parametrize("expected", [0, 2, 10])
def test_versioned_a_mismatch_changes_nothing(planner, expected):
    before = state(planner)
    with pytest.raises(VersionConflict):
        planner.reschedule("a", 50, expected_version=expected)
    assert state(planner) == before


def test_versioned_none_means_no_check(planner):
    planner.reschedule("a", 12)
    planner.reschedule("a", 0, expected_version=None)
    assert planner.get_version("a") == 3


def test_versioned_failed_moves_do_not_count(planner):
    with pytest.raises(RoomBusy):
        planner.reschedule("a", 31)
    with pytest.raises(ValueError):
        planner.reschedule("a", -1)
    with pytest.raises(VersionConflict):
        planner.reschedule("a", 0, expected_version=4)
    assert planner.get_version("a") == 1
    assert planner.get_booking("a") == ("oak", 10)


def test_versioned_conflict_class(planner):
    assert issubclass(VersionConflict, BookingError)
    assert not issubclass(VersionConflict, RoomBusy)


def test_versioned_missing_booking_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.get_version("zz")
    with pytest.raises(KeyError):
        planner.get_version(None)
    with pytest.raises(KeyError):
        planner.reschedule("zz", 0)


def test_versioned_a_busy_room_is_still_reported(planner):
    with pytest.raises(RoomBusy):
        planner.reschedule("a", 30, expected_version=1)


def test_versioned_moves_use_the_rooms_own_gap():
    p = RoomPlanner()
    p.add_room("hall", gap=2)
    p.add_room("booth")
    p.book("h1", "hall", 10)
    p.book("h2", "hall", 20)
    with pytest.raises(RoomBusy):
        p.reschedule("h2", 12)
    p.reschedule("h2", 13)
    p.book("x", "booth", 5)
    p.book("y", "booth", 8)
    p.reschedule("y", 6)
    with pytest.raises(RoomBusy):
        p.reschedule("y", 5)
    assert p.get_booking("h2") == ("hall", 13)
    assert p.get_booking("y") == ("booth", 6)


def test_versioned_new_booking_with_a_fresh_id_starts_again_at_one(planner):
    planner.reschedule("c", 0)
    planner.book("d", "elm", 10)
    assert planner.get_version("d") == 1
    assert planner.get_version("c") == 2
