"""Hidden tests for the c_cancel change (cancelling bookings). Never shown
to the writer or the editor.

Usage (with hotel.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
"""

import pytest
from hotel import Hotel, HotelError, RoomUnavailable

NIGHTS = range(1, 9)


@pytest.fixture
def hotel():
    hot = Hotel()
    hot.add_room("101")
    hot.add_room("102")
    hot.book("101", "ana", 1, 3)  # booking 1
    hot.book("101", "ben", 4, 5)  # booking 2
    hot.book("102", "cho", 2, 2)  # booking 3
    return hot


def state(hot, booking_ids=(1, 2, 3)):
    rooms = {room: [hot.get_guest(room, n) for n in NIGHTS] for room in hot.get_rooms()}
    return rooms, [hot.get_status(b) for b in booking_ids]


def test_a_cancelled_booking_gives_up_every_night(hotel):
    hotel.cancel(1)
    assert [hotel.get_guest("101", n) for n in NIGHTS] == [
        None, None, None, "ben", "ben", None, None, None,
    ]
    assert hotel.get_status(1) == "cancelled"


def test_other_bookings_are_untouched_by_a_cancellation(hotel):
    hotel.cancel(1)
    assert hotel.get_status(2) == "booked"
    assert hotel.get_status(3) == "booked"
    assert hotel.get_guest("102", 2) == "cho"


def test_freed_nights_can_be_booked_again(hotel):
    with pytest.raises(RoomUnavailable):
        hotel.book("101", "dee", 2, 3)
    hotel.cancel(1)
    assert hotel.book("101", "dee", 2, 3) == 4
    assert hotel.get_guest("101", 1) is None
    assert hotel.get_guest("101", 2) == "dee"


def test_cancelled_ids_are_never_reused(hotel):
    hotel.cancel(3)
    assert hotel.book("102", "dee", 1, 1) == 4
    hotel.cancel(4)
    assert hotel.book("102", "eve", 1, 1) == 5
    assert hotel.get_status(3) == "cancelled"
    assert hotel.get_status(4) == "cancelled"


def test_a_cancelled_booking_cannot_be_checked_in_or_out(hotel):
    hotel.cancel(1)
    with pytest.raises(HotelError):
        hotel.check_in(1)
    with pytest.raises(HotelError):
        hotel.check_out(1)
    assert hotel.get_status(1) == "cancelled"


def test_cancelling_twice_raises_and_changes_nothing(hotel):
    hotel.cancel(1)
    before = state(hotel)
    with pytest.raises(HotelError):
        hotel.cancel(1)
    assert state(hotel) == before


def test_cancelling_a_checked_in_booking_changes_nothing(hotel):
    hotel.check_in(2)
    before = state(hotel)
    with pytest.raises(HotelError):
        hotel.cancel(2)
    assert state(hotel) == before


def test_a_checked_out_booking_cannot_be_cancelled(hotel):
    hotel.check_in(2)
    hotel.check_out(2)
    before = state(hotel)
    with pytest.raises(HotelError):
        hotel.cancel(2)
    assert state(hotel) == before


@pytest.mark.parametrize("booking_id", [0, 99, None, "1"])
def test_cancelling_an_unknown_booking_raises_key_error(hotel, booking_id):
    before = state(hotel)
    with pytest.raises(KeyError):
        hotel.cancel(booking_id)
    assert state(hotel) == before


def test_a_rebooked_room_can_be_cancelled_again(hotel):
    hotel.cancel(1)
    fourth = hotel.book("101", "dee", 1, 3)
    hotel.cancel(fourth)
    assert hotel.get_guest("101", 2) is None
    assert hotel.book("101", "eve", 1, 3) == 5
    assert hotel.get_guest("101", 2) == "eve"
