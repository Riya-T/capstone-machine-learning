"""Public checks for bookings.py.

Usage (with bookings.py importable, e.g. in the sandbox):
    python -m pytest public/test_bookings_public.py
"""

import pytest
from bookings import BoxOffice, NoSeats


@pytest.fixture
def office():
    bo = BoxOffice()
    bo.add_movie("Dune")
    bo.add_movie("Heat")
    bo.add_showing("d1", "Dune", 600, 10)
    bo.add_showing("h1", "Heat", 540, 4)
    return bo


def test_a_new_showing_has_every_seat_free(office):
    assert office.get_free_seats("d1") == 10
    assert office.get_bookings("d1") == []


def test_booking_takes_seats(office):
    office.book("d1", "ann", 3)
    office.book("d1", "bob", 2)
    assert office.get_free_seats("d1") == 5
    assert office.get_bookings("d1") == [("ann", 3), ("bob", 2)]


def test_the_last_free_seats_can_be_booked(office):
    office.book("h1", "ann", 4)
    assert office.get_free_seats("h1") == 0


def test_booking_more_than_the_free_seats_raises(office):
    office.book("h1", "ann", 3)
    with pytest.raises(NoSeats):
        office.book("h1", "bob", 2)
    assert office.get_free_seats("h1") == 1
    assert office.get_bookings("h1") == [("ann", 3)]


def test_showings_are_listed_earliest_first(office):
    office.add_showing("d2", "Dune", 480, 10)
    office.add_showing("d3", "Dune", 600, 10)
    assert office.get_showings("Dune") == ["d2", "d1", "d3"]
    assert office.get_movies() == ["Dune", "Heat"]


def test_unknown_showing_raises_key_error(office):
    with pytest.raises(KeyError):
        office.get_free_seats("x9")
