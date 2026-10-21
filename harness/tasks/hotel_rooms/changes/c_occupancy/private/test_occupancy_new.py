"""Hidden tests for the c_occupancy change (occupancy figures). Never shown
to the writer or the editor.

Usage (with hotel.py importable, e.g. in the sandbox):
    python -m pytest changes/c_occupancy/private/test_occupancy_new.py
"""

import pytest
from hotel import Hotel, RoomUnavailable


@pytest.fixture
def hotel():
    hot = Hotel()
    hot.add_room("101")
    hot.add_room("102")
    hot.add_room("103")
    hot.book("101", "ana", 1, 3)  # booking 1
    hot.book("102", "ben", 2, 4)  # booking 2
    hot.book("101", "ana", 5, 5)  # booking 3
    return hot


def test_an_empty_hotel_has_no_occupancy():
    hot = Hotel()
    hot.add_room("101")
    assert hot.get_occupancy(1) == 0
    assert hot.get_nights_booked("101") == 0
    assert hot.get_guest_nights("ana") == 0


def test_occupancy_per_night(hotel):
    assert [hotel.get_occupancy(n) for n in range(1, 7)] == [1, 2, 2, 1, 1, 0]


def test_occupancy_counts_rooms_not_bookings(hotel):
    hotel.book("103", "cho", 3, 3)
    assert hotel.get_occupancy(3) == 3
    assert hotel.get_occupancy(3) <= len(hotel.get_rooms())


def test_nights_booked_sums_every_booking_of_the_room(hotel):
    assert hotel.get_nights_booked("101") == 4
    assert hotel.get_nights_booked("102") == 3
    assert hotel.get_nights_booked("103") == 0


def test_guest_nights_sum_over_rooms(hotel):
    hotel.book("103", "ben", 1, 1)
    assert hotel.get_guest_nights("ana") == 4
    assert hotel.get_guest_nights("ben") == 4
    assert hotel.get_guest_nights("cho") == 0


def test_checked_in_and_checked_out_bookings_still_count(hotel):
    hotel.check_in(1)
    hotel.check_in(2)
    hotel.check_out(2)
    assert hotel.get_occupancy(2) == 2
    assert hotel.get_nights_booked("102") == 3
    assert hotel.get_guest_nights("ben") == 3


def test_failed_bookings_change_no_figure(hotel):
    with pytest.raises(RoomUnavailable):
        hotel.book("101", "cho", 3, 4)
    with pytest.raises(ValueError):
        hotel.book("103", "", 1, 2)
    assert hotel.get_occupancy(3) == 2
    assert hotel.get_nights_booked("101") == 4
    assert hotel.get_guest_nights("cho") == 0


@pytest.mark.parametrize("night", [0, -1, 1.5, "2", None])
def test_occupancy_rejects_invalid_nights(hotel, night):
    with pytest.raises(ValueError):
        hotel.get_occupancy(night)


@pytest.mark.parametrize("room", ["999", None, 101])
def test_nights_booked_of_an_unknown_room_raises_key_error(hotel, room):
    with pytest.raises(KeyError):
        hotel.get_nights_booked(room)


def test_figures_grow_with_new_bookings(hotel):
    hotel.book("103", "ana", 1, 8)
    assert hotel.get_occupancy(7) == 1
    assert hotel.get_nights_booked("103") == 8
    assert hotel.get_guest_nights("ana") == 12
