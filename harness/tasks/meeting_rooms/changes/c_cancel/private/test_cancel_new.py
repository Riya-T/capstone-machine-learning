"""Hidden tests for the c_cancel change (cancelling bookings). Never shown to
the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
"""

import pytest
from rooms import BookingError, RoomBusy, RoomPlanner, VersionConflict


@pytest.fixture
def planner():
    p = RoomPlanner()
    p.add_room("oak")
    p.add_room("elm")
    p.book("a", "oak", 100, 160)
    p.book("b", "oak", 170, 230)
    p.book("c", "elm", 100, 160)
    return p


def state(p):
    return {
        room: (
            [(b, p.get_booking(b), p.get_version(b)) for b in p.get_room_bookings(room)],
            p.get_cancelled(room),
        )
        for room in p.get_rooms()
    }


def test_cancel_removes_only_that_booking(planner):
    planner.cancel("a")
    assert planner.get_room_bookings("oak") == ["b"]
    assert planner.get_room_bookings("elm") == ["c"]
    assert planner.get_booking("b") == ("oak", 170, 230)


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.get_booking("a"),
        lambda p: p.get_version("a"),
        lambda p: p.reschedule("a", 500, 560),
        lambda p: p.cancel("a"),
        lambda p: p.cancel("a", expected_version=1),
    ],
)
def test_cancel_a_cancelled_booking_no_longer_exists(planner, call):
    planner.cancel("a")
    before = state(planner)
    with pytest.raises(KeyError):
        call(planner)
    assert state(planner) == before


def test_cancel_frees_the_gap_too(planner):
    with pytest.raises(RoomBusy):
        planner.book("d", "oak", 165, 168)
    planner.cancel("a")
    assert planner.get_free_rooms(100, 160) == ["oak"]
    planner.book("d", "oak", 120, 160)
    assert planner.get_room_bookings("oak") == ["d", "b"]


def test_cancel_lets_another_booking_move_into_the_freed_time(planner):
    planner.cancel("b")
    planner.reschedule("a", 150, 260)
    assert planner.get_booking("a") == ("oak", 150, 260)


def test_cancel_ids_are_never_reused(planner):
    planner.cancel("a")
    before = state(planner)
    for room in ("oak", "elm"):
        with pytest.raises(BookingError) as caught:
            planner.book("a", room, 600, 660)
        assert caught.type is BookingError
    assert state(planner) == before


def test_cancel_with_the_right_expected_version(planner):
    planner.reschedule("a", 0, 60)
    planner.cancel("a", expected_version=2)
    assert planner.get_cancelled("oak") == ["a"]


def test_cancel_with_a_stale_version_changes_nothing(planner):
    planner.reschedule("a", 0, 60)
    before = state(planner)
    with pytest.raises(VersionConflict):
        planner.cancel("a", expected_version=1)
    assert state(planner) == before


def test_cancel_missing_booking_is_reported_before_a_conflict(planner):
    with pytest.raises(KeyError):
        planner.cancel("zz", expected_version=5)
    with pytest.raises(KeyError):
        planner.cancel(None)


def test_cancelled_lists_follow_cancel_order_per_room(planner):
    planner.book("d", "oak", 400, 460)
    planner.cancel("d")
    planner.cancel("c")
    planner.cancel("a")
    assert planner.get_cancelled("oak") == ["d", "a"]
    assert planner.get_cancelled("elm") == ["c"]


def test_cancelled_list_of_a_room_without_cancellations_is_empty(planner):
    assert planner.get_cancelled("oak") == []
    planner.add_room("pine")
    assert planner.get_cancelled("pine") == []


def test_cancelled_list_of_a_missing_room_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.get_cancelled("pine")
    with pytest.raises(KeyError):
        planner.get_cancelled(1)


def test_cancel_other_versions_are_untouched(planner):
    planner.reschedule("b", 180, 240)
    planner.cancel("a")
    assert planner.get_version("b") == 2
    assert planner.get_version("c") == 1
