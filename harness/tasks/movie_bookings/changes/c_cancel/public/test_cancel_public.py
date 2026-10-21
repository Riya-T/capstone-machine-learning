"""Public checks for the c_cancel change (cancelling bookings). Shown to the
editor, never to the writer.

Usage (with bookings.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/public/test_cancel_public.py
"""

import pytest
from bookings import BookingError, BoxOffice


@pytest.fixture
def office():
    bo = BoxOffice()
    bo.add_movie("Dune")
    bo.add_showing("d1", "Dune", 600, 10)
    return bo


def test_cancelling_frees_the_seats(office):
    office.book("d1", "ann", 3)
    office.book("d1", "bob", 2)
    assert office.cancel("d1", "ann") == 3
    assert office.get_free_seats("d1") == 8
    assert office.get_bookings("d1") == [("bob", 2)]
    assert office.get_cancelled("d1") == [("ann", 3)]


def test_cancelling_without_a_booking_raises(office):
    office.book("d1", "ann", 3)
    with pytest.raises(BookingError):
        office.cancel("d1", "bob")
    assert office.get_free_seats("d1") == 7
