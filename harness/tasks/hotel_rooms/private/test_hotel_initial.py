"""Hidden tests for the initial hotel_rooms spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with hotel.py importable, e.g. in the sandbox):
    python -m pytest private/test_hotel_initial.py
"""

import pytest
from hotel import Hotel, HotelError, RoomUnavailable

NIGHTS = range(1, 9)
BAD_GUESTS = ["", None, 5]
BAD_NIGHTS = [(0, 1), (1, 0), (3, 2), (-1, 3), (1.5, 2), (1, 2.5), ("1", 2), (1, None)]
BAD_IDS = [0, 99, -1, None, "1"]


@pytest.fixture
def hotel():
    hot = Hotel()
    hot.add_room("101")
    hot.add_room("102")
    return hot


def state(hot, booking_ids=()):
    """Who holds every room on nights 1-8, plus each booking's status, to
    check that a failed call changed nothing."""
    rooms = {room: [hot.get_guest(room, n) for n in NIGHTS] for room in hot.get_rooms()}
    return rooms, [hot.get_status(b) for b in booking_ids]


# --- rooms ------------------------------------------------------------------


def test_rooms_are_listed_in_the_order_added():
    hot = Hotel()
    for room in ["203", "101", "102"]:
        hot.add_room(room)
    assert hot.get_rooms() == ["203", "101", "102"]


def test_a_new_room_has_no_guests(hotel):
    assert all(hotel.get_guest("101", n) is None for n in NIGHTS)


@pytest.mark.parametrize("bad_room", [""])
def test_invalid_room_names_are_rejected(bad_room):
    hot = Hotel()
    with pytest.raises(ValueError):
        hot.add_room(bad_room)
    assert hot.get_rooms() == []


def test_adding_an_existing_room_is_rejected(hotel):
    hotel.book("101", "ana", 1, 2)
    with pytest.raises(HotelError):
        hotel.add_room("101")
    assert hotel.get_rooms() == ["101", "102"]
    assert hotel.get_guest("101", 1) == "ana"


@pytest.mark.parametrize(
    "call",
    [
        lambda hot: hot.book("303", "ana", 1, 2),
        lambda hot: hot.get_guest("303", 1),
        lambda hot: hot.get_guest(None, 1),
        lambda hot: hot.get_guest(101, 1),
        lambda hot: hot.book(None, "ana", 1, 2),
    ],
)
def test_rooms_that_do_not_exist_raise_key_error(hotel, call):
    hotel.book("101", "ana", 1, 2)
    before = state(hotel, [1])
    with pytest.raises(KeyError):
        call(hotel)
    assert state(hotel, [1]) == before


# --- bookings ---------------------------------------------------------------


def test_booking_ids_count_up_from_one(hotel):
    assert hotel.book("101", "ana", 1, 1) == 1
    assert hotel.book("102", "ben", 1, 1) == 2
    assert hotel.book("101", "cho", 2, 2) == 3


def test_a_failed_booking_uses_no_id(hotel):
    hotel.book("101", "ana", 1, 3)
    with pytest.raises(RoomUnavailable):
        hotel.book("101", "ben", 3, 4)
    assert hotel.book("102", "ben", 3, 4) == 2


def test_every_night_of_the_range_is_booked_including_both_ends(hotel):
    hotel.book("101", "ana", 2, 4)
    assert [hotel.get_guest("101", n) for n in NIGHTS] == [
        None, "ana", "ana", "ana", None, None, None, None,
    ]


def test_a_single_night_booking(hotel):
    hotel.book("101", "ana", 5, 5)
    assert hotel.get_guest("101", 5) == "ana"
    assert hotel.get_guest("101", 4) is None
    assert hotel.get_guest("101", 6) is None


def test_overlapping_only_on_the_last_night_is_refused(hotel):
    hotel.book("101", "ana", 1, 3)
    before = state(hotel, [1])
    with pytest.raises(RoomUnavailable):
        hotel.book("101", "ben", 3, 5)
    assert state(hotel, [1]) == before


def test_overlapping_only_on_the_first_night_is_refused(hotel):
    hotel.book("101", "ana", 3, 5)
    with pytest.raises(RoomUnavailable):
        hotel.book("101", "ben", 1, 3)
    assert hotel.get_guest("101", 3) == "ana"


def test_a_booking_enclosing_another_is_refused(hotel):
    hotel.book("101", "ana", 3, 3)
    with pytest.raises(RoomUnavailable):
        hotel.book("101", "ben", 1, 6)
    assert hotel.get_guest("101", 1) is None
    assert hotel.get_guest("101", 3) == "ana"


def test_bookings_that_touch_do_not_overlap(hotel):
    hotel.book("101", "ana", 1, 3)
    hotel.book("101", "ben", 4, 5)
    assert hotel.get_guest("101", 3) == "ana"
    assert hotel.get_guest("101", 4) == "ben"


def test_other_rooms_are_not_affected_by_a_booking(hotel):
    hotel.book("101", "ana", 1, 3)
    hotel.book("102", "ana", 1, 3)
    assert hotel.get_guest("101", 2) == "ana"
    assert hotel.get_guest("102", 2) == "ana"


@pytest.mark.parametrize("guest", BAD_GUESTS)
def test_invalid_guests_are_rejected(hotel, guest):
    before = state(hotel)
    with pytest.raises(ValueError):
        hotel.book("101", guest, 1, 2)
    assert state(hotel) == before


@pytest.mark.parametrize("first, last", BAD_NIGHTS)
def test_invalid_nights_are_rejected(hotel, first, last):
    before = state(hotel)
    with pytest.raises(ValueError):
        hotel.book("101", "ana", first, last)
    assert state(hotel) == before


@pytest.mark.parametrize("night", [0, -2, 1.5, "1", None])
def test_get_guest_rejects_invalid_nights(hotel, night):
    with pytest.raises(ValueError):
        hotel.get_guest("101", night)


def test_a_missing_room_is_reported_before_a_bad_guest(hotel):
    with pytest.raises(KeyError):
        hotel.book("303", "", 1, 2)
    with pytest.raises(KeyError):
        hotel.book("303", "ana", 0, 2)


def test_a_bad_guest_is_reported_before_bad_nights(hotel):
    with pytest.raises(ValueError):
        hotel.book("101", "", 2, 1)


def test_bad_nights_are_reported_before_an_unavailable_room(hotel):
    hotel.book("101", "ana", 1, 3)
    with pytest.raises(ValueError):
        hotel.book("101", "ben", 3, 1)


# --- checking in and out ----------------------------------------------------


def test_status_moves_from_booked_to_checked_out(hotel):
    first = hotel.book("101", "ana", 1, 2)
    second = hotel.book("102", "ben", 1, 2)
    hotel.check_in(first)
    assert hotel.get_status(first) == "checked_in"
    assert hotel.get_status(second) == "booked"
    hotel.check_out(first)
    assert hotel.get_status(first) == "checked_out"
    assert hotel.get_status(second) == "booked"


def test_checking_out_keeps_the_nights(hotel):
    booking = hotel.book("101", "ana", 1, 2)
    hotel.check_in(booking)
    hotel.check_out(booking)
    assert hotel.get_guest("101", 1) == "ana"
    with pytest.raises(RoomUnavailable):
        hotel.book("101", "ben", 2, 3)


def test_check_in_is_only_allowed_once(hotel):
    booking = hotel.book("101", "ana", 1, 2)
    hotel.check_in(booking)
    with pytest.raises(HotelError):
        hotel.check_in(booking)
    assert hotel.get_status(booking) == "checked_in"
    hotel.check_out(booking)
    with pytest.raises(HotelError):
        hotel.check_in(booking)
    assert hotel.get_status(booking) == "checked_out"


def test_check_out_needs_a_check_in(hotel):
    booking = hotel.book("101", "ana", 1, 2)
    with pytest.raises(HotelError):
        hotel.check_out(booking)
    assert hotel.get_status(booking) == "booked"
    hotel.check_in(booking)
    hotel.check_out(booking)
    with pytest.raises(HotelError):
        hotel.check_out(booking)
    assert hotel.get_status(booking) == "checked_out"


@pytest.mark.parametrize("booking_id", BAD_IDS)
@pytest.mark.parametrize("method", ["check_in", "check_out", "get_status"])
def test_unknown_booking_ids_raise_key_error(hotel, method, booking_id):
    hotel.book("101", "ana", 1, 2)
    before = state(hotel, [1])
    with pytest.raises(KeyError):
        getattr(hotel, method)(booking_id)
    assert state(hotel, [1]) == before


def test_room_unavailable_is_a_hotel_error():
    assert issubclass(RoomUnavailable, HotelError)


def test_hotels_do_not_share_rooms_or_bookings():
    first, second = Hotel(), Hotel()
    first.add_room("101")
    first.book("101", "ana", 1, 2)
    assert second.get_rooms() == []
    second.add_room("101")
    assert second.get_guest("101", 1) is None
    assert second.book("101", "ben", 1, 2) == 1
