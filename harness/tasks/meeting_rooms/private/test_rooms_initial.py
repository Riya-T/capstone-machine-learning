"""Hidden tests for the initial meeting_rooms spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest private/test_rooms_initial.py
"""

import pytest
from rooms import BookingError, RoomBusy, RoomPlanner

BAD_TIMES = [(-1, 30), (30, 30), (40, 30), (1.5, 30), (0, 30.0), ("0", 30), (0, None)]


@pytest.fixture
def planner():
    p = RoomPlanner()
    p.add_room("oak")
    p.add_room("elm")
    p.book("a", "oak", 100, 160)
    return p


def state(p):
    """Every room's bookings and their times, to check that a failed call
    changed nothing."""
    return {
        room: [(b, p.get_booking(b)) for b in p.get_room_bookings(room)]
        for room in p.get_rooms()
    }


# --- rooms ------------------------------------------------------------------


def test_rooms_are_listed_in_the_order_added():
    p = RoomPlanner()
    for name in ["pine", "ash", "birch"]:
        p.add_room(name)
    assert p.get_rooms() == ["pine", "ash", "birch"]


def test_an_empty_room_name_is_rejected():
    p = RoomPlanner()
    with pytest.raises(ValueError):
        p.add_room("")
    assert p.get_rooms() == []


def test_adding_a_room_twice_is_rejected(planner):
    before = state(planner)
    with pytest.raises(BookingError):
        planner.add_room("oak")
    assert state(planner) == before
    assert planner.get_rooms() == ["oak", "elm"]


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.book("b", "pine", 0, 30),
        lambda p: p.get_room_bookings("pine"),
        lambda p: p.get_booking("zz"),
        lambda p: p.reschedule("zz", 0, 30),
        lambda p: p.get_booking(None),
        lambda p: p.get_room_bookings(1),
    ],
)
def test_rooms_and_bookings_that_do_not_exist_raise_key_error(planner, call):
    before = state(planner)
    with pytest.raises(KeyError):
        call(planner)
    assert state(planner) == before


# --- booking ----------------------------------------------------------------


def test_bookings_in_different_rooms_do_not_interfere(planner):
    planner.book("b", "elm", 100, 160)
    planner.book("c", "elm", 170, 200)
    assert planner.get_room_bookings("elm") == ["b", "c"]
    assert planner.get_booking("b") == ("elm", 100, 160)


def test_a_booking_exactly_ten_minutes_later_is_allowed(planner):
    planner.book("b", "oak", 170, 200)
    planner.book("c", "oak", 50, 90)
    assert planner.get_room_bookings("oak") == ["c", "a", "b"]


@pytest.mark.parametrize(
    "start,end",
    [(169, 200), (50, 91), (120, 140), (90, 300), (0, 100), (160, 170), (159, 165)],
)
def test_bookings_too_close_or_overlapping_are_refused(planner, start, end):
    before = state(planner)
    with pytest.raises(RoomBusy):
        planner.book("b", "oak", start, end)
    assert state(planner) == before


def test_a_one_minute_booking_works():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("x", "oak", 0, 1)
    p.book("y", "oak", 11, 12)
    assert p.get_booking("y") == ("oak", 11, 12)


@pytest.mark.parametrize("start,end", BAD_TIMES)
def test_invalid_times_are_rejected(planner, start, end):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.book("b", "elm", start, end)
    with pytest.raises(ValueError):
        planner.reschedule("a", start, end)
    with pytest.raises(ValueError):
        planner.get_free_rooms(start, end)
    assert state(planner) == before


@pytest.mark.parametrize("booking_id", ["", None, 5])
def test_invalid_booking_ids_are_rejected(planner, booking_id):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.book(booking_id, "elm", 0, 30)
    assert state(planner) == before


def test_a_booking_id_is_unique_across_rooms(planner):
    before = state(planner)
    with pytest.raises(BookingError) as caught:
        planner.book("a", "elm", 500, 530)
    assert caught.type is BookingError
    assert state(planner) == before


def test_error_precedence_when_booking(planner):
    with pytest.raises(KeyError):
        planner.book("", "pine", -5, 0)
    with pytest.raises(ValueError):
        planner.book("", "oak", 100, 160)
    with pytest.raises(ValueError):
        planner.book("a", "oak", 100, 90)
    with pytest.raises(BookingError) as caught:
        planner.book("a", "oak", 100, 160)
    assert caught.type is BookingError


def test_room_busy_is_a_booking_error():
    assert issubclass(RoomBusy, BookingError)


# --- rescheduling -----------------------------------------------------------


def test_reschedule_moves_the_booking(planner):
    planner.reschedule("a", 400, 430)
    assert planner.get_booking("a") == ("oak", 400, 430)
    planner.book("b", "oak", 100, 160)
    assert planner.get_room_bookings("oak") == ["b", "a"]


def test_reschedule_to_the_same_times_is_allowed(planner):
    planner.reschedule("a", 100, 160)
    assert planner.get_booking("a") == ("oak", 100, 160)


def test_reschedule_respects_the_gap_to_other_bookings(planner):
    planner.book("b", "oak", 200, 260)
    before = state(planner)
    with pytest.raises(RoomBusy):
        planner.reschedule("a", 150, 195)
    assert state(planner) == before
    planner.reschedule("a", 120, 190)
    assert planner.get_booking("a") == ("oak", 120, 190)


def test_reschedule_frees_the_old_times(planner):
    planner.reschedule("a", 500, 560)
    planner.book("b", "oak", 100, 160)
    assert planner.get_free_rooms(300, 330) == ["oak", "elm"]


def test_a_missing_booking_is_reported_before_bad_times(planner):
    with pytest.raises(KeyError):
        planner.reschedule("zz", -1, -5)


def test_bad_times_are_reported_before_a_busy_room(planner):
    planner.book("b", "oak", 200, 260)
    with pytest.raises(ValueError):
        planner.reschedule("b", 100, 100)


# --- free rooms ---------------------------------------------------------------


def test_free_rooms_respect_the_gap(planner):
    assert planner.get_free_rooms(165, 200) == ["elm"]
    assert planner.get_free_rooms(170, 200) == ["oak", "elm"]
    assert planner.get_free_rooms(40, 91) == ["elm"]
    assert planner.get_free_rooms(40, 90) == ["oak", "elm"]


def test_free_rooms_change_nothing(planner):
    before = state(planner)
    planner.get_free_rooms(0, 1000)
    assert state(planner) == before


def test_planners_do_not_share_rooms():
    first, second = RoomPlanner(), RoomPlanner()
    first.add_room("oak")
    assert second.get_rooms() == []
    second.add_room("oak")
    second.book("a", "oak", 0, 10)
    first.book("a", "oak", 0, 10)
