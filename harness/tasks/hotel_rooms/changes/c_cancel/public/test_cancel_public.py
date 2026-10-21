"""Public checks for the c_cancel change (cancelling bookings). Shown to the
editor, never to the writer.

Usage (with hotel.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/public/test_cancel_public.py
"""

import pytest
from hotel import Hotel, HotelError


def test_cancelling_frees_the_nights():
    hot = Hotel()
    hot.add_room("101")
    booking = hot.book("101", "ana", 1, 3)
    hot.cancel(booking)
    assert hot.get_status(booking) == "cancelled"
    assert hot.get_guest("101", 2) is None
    assert hot.book("101", "ben", 2, 4) == 2


def test_a_checked_in_booking_cannot_be_cancelled():
    hot = Hotel()
    hot.add_room("101")
    booking = hot.book("101", "ana", 1, 3)
    hot.check_in(booking)
    with pytest.raises(HotelError):
        hot.cancel(booking)
    assert hot.get_status(booking) == "checked_in"
