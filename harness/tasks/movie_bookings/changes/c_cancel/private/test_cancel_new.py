"""Hidden tests for the c_cancel change (cancelling bookings). Never shown to
the writer or the editor.

Usage (with bookings.py importable, e.g. in the sandbox):
    python -m pytest changes/c_cancel/private/test_cancel_new.py
"""

import pytest
from bookings import BookingError, BoxOffice, NoSeats


@pytest.fixture
def office():
    bo = BoxOffice()
    bo.add_movie("Dune")
    bo.add_movie("Heat")
    bo.add_showing("d1", "Dune", 600, 10)
    bo.add_showing("h1", "Heat", 540, 4)
    bo.book("d1", "ann", 2)
    bo.book("d1", "bob", 3)
    bo.book("d1", "ann", 1)
    return bo


def state(bo):
    return {
        sid: (bo.get_free_seats(sid), bo.get_bookings(sid), bo.get_cancelled(sid))
        for title in bo.get_movies()
        for sid in bo.get_showings(title)
    }


def test_nothing_is_cancelled_to_begin_with(office):
    assert office.get_cancelled("d1") == []
    assert office.get_cancelled("h1") == []


def test_the_most_recent_booking_of_the_customer_goes_first(office):
    assert office.cancel("d1", "ann") == 1
    assert office.get_bookings("d1") == [("ann", 2), ("bob", 3)]
    assert office.get_free_seats("d1") == 5
    assert office.cancel("d1", "ann") == 2
    assert office.get_bookings("d1") == [("bob", 3)]
    assert office.get_free_seats("d1") == 7


def test_cancelled_list_keeps_cancellation_order(office):
    office.cancel("d1", "bob")
    office.cancel("d1", "ann")
    office.cancel("d1", "ann")
    assert office.get_cancelled("d1") == [("bob", 3), ("ann", 1), ("ann", 2)]
    assert office.get_bookings("d1") == []
    assert office.get_free_seats("d1") == 10


def test_freed_seats_can_be_booked_again(office):
    office.book("h1", "cat", 4)
    with pytest.raises(NoSeats):
        office.book("h1", "dan", 1)
    office.cancel("h1", "cat")
    office.book("h1", "dan", 4)
    assert office.get_bookings("h1") == [("dan", 4)]
    assert office.get_cancelled("h1") == [("cat", 4)]


def test_cancelling_leaves_other_showings_alone(office):
    office.book("h1", "ann", 1)
    office.cancel("d1", "ann")
    assert office.get_bookings("h1") == [("ann", 1)]
    assert office.get_cancelled("h1") == []
    assert office.get_free_seats("h1") == 3


def test_a_customer_with_no_booking_left_cannot_cancel(office):
    office.cancel("d1", "bob")
    before = state(office)
    with pytest.raises(BookingError):
        office.cancel("d1", "bob")
    with pytest.raises(BookingError):
        office.cancel("h1", "ann")
    assert state(office) == before


@pytest.mark.parametrize("showing_id", ["x9", None, 1])
def test_cancel_on_an_unknown_showing_raises_key_error(office, showing_id):
    before = state(office)
    with pytest.raises(KeyError):
        office.cancel(showing_id, "ann")
    with pytest.raises(KeyError):
        office.get_cancelled(showing_id)
    assert state(office) == before


@pytest.mark.parametrize("customer", ["", None, 7])
def test_cancel_with_an_invalid_customer_raises_value_error(office, customer):
    before = state(office)
    with pytest.raises(ValueError):
        office.cancel("d1", customer)
    assert state(office) == before


def test_an_unknown_showing_is_reported_before_an_invalid_customer_when_cancelling(office):
    with pytest.raises(KeyError):
        office.cancel("x9", "")


def test_an_invalid_customer_is_reported_before_a_missing_booking(office):
    with pytest.raises(ValueError):
        office.cancel("h1", "")
