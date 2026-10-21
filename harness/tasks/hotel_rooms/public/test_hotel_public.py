"""Public checks for hotel.py.

Usage (with hotel.py importable, e.g. in the sandbox):
    python -m pytest public/test_hotel_public.py
"""

import pytest
from hotel import Hotel, HotelError, RoomUnavailable


@pytest.fixture
def hotel():
    hot = Hotel()
    hot.add_room("101")
    hot.add_room("102")
    return hot


def test_booking_returns_increasing_ids(hotel):
    assert hotel.book("101", "ana", 1, 3) == 1
    assert hotel.book("102", "ben", 1, 1) == 2


def test_the_guest_is_found_on_a_booked_night(hotel):
    hotel.book("101", "ana", 2, 4)
    assert hotel.get_guest("101", 3) == "ana"
    assert hotel.get_guest("101", 1) is None
    assert hotel.get_guest("102", 3) is None


def test_a_room_cannot_be_booked_twice_for_the_same_night(hotel):
    hotel.book("101", "ana", 1, 3)
    with pytest.raises(RoomUnavailable):
        hotel.book("101", "ben", 2, 5)
    assert hotel.get_guest("101", 2) == "ana"


def test_check_in_then_check_out(hotel):
    booking = hotel.book("101", "ana", 1, 2)
    assert hotel.get_status(booking) == "booked"
    hotel.check_in(booking)
    assert hotel.get_status(booking) == "checked_in"
    hotel.check_out(booking)
    assert hotel.get_status(booking) == "checked_out"


def test_checking_in_twice_raises(hotel):
    booking = hotel.book("101", "ana", 1, 2)
    hotel.check_in(booking)
    with pytest.raises(HotelError):
        hotel.check_in(booking)


def test_unknown_room_raises_key_error(hotel):
    with pytest.raises(KeyError):
        hotel.book("303", "ana", 1, 2)
    with pytest.raises(KeyError):
        hotel.get_guest("303", 1)
