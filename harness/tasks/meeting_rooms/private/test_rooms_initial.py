"""Hidden tests for the initial meeting_rooms spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with rooms.py importable, e.g. in the sandbox):
    python -m pytest private/test_rooms_initial.py
"""

import pytest
from rooms import BookingError, RoomBusy, RoomPlanner


def room_bookings(p, room):
    """The ids of the room's bookings, read through get_bookings()."""
    return [b for b in p.get_bookings() if p.get_booking(b)[0] == room]


@pytest.fixture
def planner():
    p = RoomPlanner()
    p.add_room("oak")
    p.add_room("elm")
    p.book("a", "oak", 10)
    return p


def state(p):
    """Every room's bookings and their slots, to check that a failed call
    changed nothing."""
    return {
        room: sorted((b, p.get_booking(b)) for b in room_bookings(p, room))
        for room in p.get_rooms()
    }


# --- rooms ------------------------------------------------------------------


def test_rooms_are_listed_in_the_order_added():
    p = RoomPlanner()
    for name in ["pine", "ash", "birch"]:
        p.add_room(name)
    assert p.get_rooms() == ["pine", "ash", "birch"]
    assert p.get_bookings() == []


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
        lambda p: p.book("b", "pine", 0),
        lambda p: p.get_booking("zz"),
        lambda p: p.get_booking(None),
        lambda p: p.get_booking(1),
    ],
)
def test_rooms_and_bookings_that_do_not_exist_raise_key_error(planner, call):
    before = state(planner)
    with pytest.raises(KeyError):
        call(planner)
    assert state(planner) == before


# --- booking ----------------------------------------------------------------


def test_bookings_in_different_rooms_do_not_interfere(planner):
    planner.book("b", "elm", 10)
    planner.book("c", "elm", 12)
    assert sorted(room_bookings(planner, "elm")) == ["b", "c"]
    assert planner.get_booking("b") == ("elm", 10)
    assert room_bookings(planner, "oak") == ["a"]


def test_neighbouring_slots_can_be_booked(planner):
    planner.book("b", "oak", 11)
    planner.book("c", "oak", 9)
    planner.book("d", "oak", 12)
    assert sorted(room_bookings(planner, "oak")) == ["a", "b", "c", "d"]
    assert planner.get_booking("c") == ("oak", 9)


def test_a_booked_slot_is_refused(planner):
    before = state(planner)
    with pytest.raises(RoomBusy):
        planner.book("b", "oak", 10)
    assert state(planner) == before


def test_each_booking_is_checked_against_every_booking_of_the_room():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("a", "oak", 2)
    p.book("b", "oak", 6)
    p.book("c", "oak", 10)
    for slot in (2, 6, 10):
        with pytest.raises(RoomBusy):
            p.book("d", "oak", slot)
    p.book("d", "oak", 3)
    p.book("e", "oak", 7)
    with pytest.raises(RoomBusy):
        p.book("f", "oak", 3)
    assert sorted(room_bookings(p, "oak")) == ["a", "b", "c", "d", "e"]


def test_slot_zero_can_be_booked():
    p = RoomPlanner()
    p.add_room("oak")
    p.book("x", "oak", 0)
    with pytest.raises(RoomBusy):
        p.book("y", "oak", 0)
    p.book("y", "oak", 1)
    assert p.get_booking("x") == ("oak", 0)
    assert p.get_booking("y") == ("oak", 1)


@pytest.mark.parametrize("slot", [-1, -5])
def test_slots_below_zero_are_rejected(planner, slot):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.book("b", "elm", slot)
    with pytest.raises(ValueError):
        planner.get_free_rooms(slot)
    assert state(planner) == before


@pytest.mark.parametrize("booking_id", ["", None])
def test_invalid_booking_ids_are_rejected(planner, booking_id):
    before = state(planner)
    with pytest.raises(ValueError):
        planner.book(booking_id, "elm", 0)
    assert state(planner) == before


def test_a_booking_id_is_unique_across_rooms(planner):
    before = state(planner)
    with pytest.raises(BookingError) as caught:
        planner.book("a", "elm", 30)
    assert caught.type is BookingError
    assert state(planner) == before


def test_a_refused_booking_uses_up_no_id(planner):
    with pytest.raises(RoomBusy):
        planner.book("b", "oak", 10)
    with pytest.raises(KeyError):
        planner.get_booking("b")
    planner.book("b", "oak", 11)
    assert planner.get_booking("b") == ("oak", 11)


def test_room_busy_is_a_booking_error():
    assert issubclass(RoomBusy, BookingError)


# --- free rooms ---------------------------------------------------------------


def test_free_rooms_only_skip_the_booked_slot(planner):
    assert planner.get_free_rooms(10) == ["elm"]
    assert planner.get_free_rooms(11) == ["oak", "elm"]
    assert planner.get_free_rooms(9) == ["oak", "elm"]


def test_free_rooms_follow_new_bookings(planner):
    planner.book("b", "elm", 20)
    planner.book("c", "oak", 30)
    assert planner.get_free_rooms(20) == ["oak"]
    assert planner.get_free_rooms(21) == ["oak", "elm"]
    assert planner.get_free_rooms(10) == ["elm"]
    planner.book("d", "oak", 20)
    assert planner.get_free_rooms(20) == []
    assert planner.get_free_rooms(30) == ["elm"]


def test_free_rooms_change_nothing(planner):
    before = state(planner)
    planner.get_free_rooms(10)
    planner.get_free_rooms(0)
    assert state(planner) == before


def test_planners_do_not_share_rooms():
    first, second = RoomPlanner(), RoomPlanner()
    first.add_room("oak")
    assert second.get_rooms() == []
    second.add_room("oak")
    second.book("a", "oak", 0)
    first.book("a", "oak", 0)
