"""Hidden tests for the c_cancel change (cancelling bookings).
Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
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
    p.book("b", "oak", 12)
    p.book("c", "elm", 10)
    return p


def state(p):
    return {
        room: (
            sorted((b, p.get_booking(b), p.get_version(b)) for b in room_bookings(p, room)),
            p.get_cancelled(room),
        )
        for room in p.get_rooms()
    }


def test_cancel_removes_only_that_booking(planner):
    planner.cancel("a")
    assert room_bookings(planner, "oak") == ["b"]
    assert room_bookings(planner, "elm") == ["c"]
    assert planner.get_booking("b") == ("oak", 12)


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.get_booking("a"),
        lambda p: p.get_version("a"),
        lambda p: p.reschedule("a", 30),
        lambda p: p.cancel("a"),
    ],
)
def test_cancel_a_cancelled_booking_no_longer_exists(planner, call):
    planner.cancel("a")
    before = state(planner)
    with pytest.raises(KeyError):
        call(planner)
    assert state(planner) == before


def test_cancel_frees_the_slot(planner):
    with pytest.raises(RoomBusy):
        planner.book("d", "elm", 10)
    planner.cancel("c")
    assert planner.get_free_rooms(10) == ["elm"]
    planner.book("d", "elm", 10)
    assert room_bookings(planner, "elm") == ["d"]


def test_cancel_frees_the_slots_its_gap_kept_free(planner):
    with pytest.raises(RoomBusy):
        planner.book("d", "oak", 9)
    planner.cancel("a")
    planner.book("d", "oak", 9)
    with pytest.raises(RoomBusy):
        planner.book("e", "oak", 11)
    assert sorted(room_bookings(planner, "oak")) == ["b", "d"]


def test_cancel_lets_another_booking_move_into_the_freed_slot(planner):
    planner.cancel("b")
    planner.reschedule("a", 12)
    assert planner.get_booking("a") == ("oak", 12)
    planner.cancel("c")
    planner.book("e", "elm", 10)


def test_cancel_ids_are_never_reused(planner):
    planner.cancel("a")
    before = state(planner)
    for room in ("oak", "elm"):
        with pytest.raises(BookingError) as caught:
            planner.book("a", room, 40)
        assert caught.type is BookingError
    assert state(planner) == before


def test_cancel_with_the_right_expected_version(planner):
    planner.reschedule("a", 6)
    planner.cancel("a", expected_version=2)
    assert planner.get_cancelled("oak") == ["a"]


def test_cancel_with_a_stale_version_changes_nothing(planner):
    planner.reschedule("a", 6)
    before = state(planner)
    with pytest.raises(VersionConflict):
        planner.cancel("a", expected_version=1)
    assert state(planner) == before


def test_cancel_missing_booking_raises_key_error(planner):
    with pytest.raises(KeyError):
        planner.cancel("zz")
    with pytest.raises(KeyError):
        planner.cancel(None)


def test_cancelled_lists_follow_cancel_order_per_room(planner):
    planner.book("d", "oak", 20)
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
    planner.reschedule("b", 14)
    planner.cancel("a")
    assert planner.get_version("b") == 2
    assert planner.get_version("c") == 1
