"""Hidden tests for the initial movie_bookings spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with bookings.py importable, e.g. in the sandbox):
    python -m pytest private/test_bookings_initial.py
"""

import pytest
from bookings import BookingError, BoxOffice, NoSeats

BAD_STARTS = [-1, 1.5, "600", None, True]
BAD_SEATS = [0, -3, 2.5, "4", None, True]
BAD_CUSTOMERS = ["", None, 7]


@pytest.fixture
def office():
    bo = BoxOffice()
    bo.add_movie("Dune")
    bo.add_movie("Heat")
    bo.add_showing("d1", "Dune", 600, 10)
    bo.add_showing("h1", "Heat", 540, 4)
    return bo


def state(bo):
    """Every showing's free seats and bookings, to check that a failed call
    changed nothing."""
    return {
        title: [(sid, bo.get_free_seats(sid), bo.get_bookings(sid)) for sid in bo.get_showings(title)]
        for title in bo.get_movies()
    }


# --- movies -----------------------------------------------------------------


def test_movies_are_listed_in_the_order_added():
    bo = BoxOffice()
    for title in ["Heat", "Alien", "Dune"]:
        bo.add_movie(title)
    assert bo.get_movies() == ["Heat", "Alien", "Dune"]


def test_an_empty_title_is_rejected():
    bo = BoxOffice()
    with pytest.raises(ValueError):
        bo.add_movie("")
    assert bo.get_movies() == []


def test_adding_a_movie_twice_is_rejected(office):
    with pytest.raises(BookingError):
        office.add_movie("Dune")
    assert office.get_movies() == ["Dune", "Heat"]
    assert office.get_showings("Dune") == ["d1"]


def test_a_movie_without_showings_has_an_empty_list(office):
    office.add_movie("Alien")
    assert office.get_showings("Alien") == []


@pytest.mark.parametrize("title", ["Alien", None, 3])
def test_titles_that_were_not_added_raise_key_error(office, title):
    before = state(office)
    with pytest.raises(KeyError):
        office.get_showings(title)
    with pytest.raises(KeyError):
        office.add_showing("x1", title, 600, 5)
    assert state(office) == before


# --- showings ---------------------------------------------------------------


def test_a_new_showing_starts_with_all_seats_free(office):
    office.add_showing("d2", "Dune", 900, 25)
    assert office.get_free_seats("d2") == 25
    assert office.get_bookings("d2") == []


def test_showings_are_sorted_by_start_with_ties_in_added_order(office):
    office.add_showing("d2", "Dune", 480, 10)
    office.add_showing("d3", "Dune", 600, 10)
    office.add_showing("d4", "Dune", 480, 10)
    office.add_showing("h2", "Heat", 0, 10)
    assert office.get_showings("Dune") == ["d2", "d4", "d1", "d3"]
    assert office.get_showings("Heat") == ["h2", "h1"]


def test_an_empty_showing_id_is_rejected(office):
    before = state(office)
    with pytest.raises(ValueError):
        office.add_showing("", "Dune", 600, 5)
    assert state(office) == before


def test_a_showing_id_cannot_be_used_twice(office):
    office.book("d1", "ann", 2)
    before = state(office)
    with pytest.raises(BookingError):
        office.add_showing("d1", "Heat", 700, 50)
    assert state(office) == before
    assert office.get_showings("Heat") == ["h1"]


@pytest.mark.parametrize("start", BAD_STARTS)
def test_invalid_starts_are_rejected(office, start):
    before = state(office)
    with pytest.raises(ValueError):
        office.add_showing("d2", "Dune", start, 5)
    assert state(office) == before


@pytest.mark.parametrize("seats", BAD_SEATS)
def test_invalid_seat_counts_are_rejected_for_showings(office, seats):
    before = state(office)
    with pytest.raises(ValueError):
        office.add_showing("d2", "Dune", 600, seats)
    assert state(office) == before


def test_a_showing_can_start_at_midnight(office):
    office.add_showing("d0", "Dune", 0, 1)
    assert office.get_showings("Dune") == ["d0", "d1"]


@pytest.mark.parametrize(
    "call",
    [
        lambda bo: bo.book("x9", "ann", 1),
        lambda bo: bo.get_free_seats("x9"),
        lambda bo: bo.get_bookings("x9"),
        lambda bo: bo.get_free_seats(None),
        lambda bo: bo.get_bookings(1),
        lambda bo: bo.book(None, "ann", 1),
    ],
)
def test_showings_that_were_not_added_raise_key_error(office, call):
    office.book("d1", "ann", 2)
    before = state(office)
    with pytest.raises(KeyError):
        call(office)
    assert state(office) == before


# --- bookings ---------------------------------------------------------------


def test_bookings_reduce_the_free_seats(office):
    office.book("d1", "ann", 4)
    office.book("d1", "bob", 1)
    assert office.get_free_seats("d1") == 5
    assert office.get_free_seats("h1") == 4


def test_every_seat_can_be_booked(office):
    office.book("h1", "ann", 3)
    office.book("h1", "bob", 1)
    assert office.get_free_seats("h1") == 0


def test_overbooking_raises_and_changes_nothing(office):
    office.book("h1", "ann", 3)
    before = state(office)
    with pytest.raises(NoSeats):
        office.book("h1", "bob", 2)
    with pytest.raises(NoSeats):
        office.book("d1", "bob", 11)
    assert state(office) == before


def test_bookings_are_listed_in_order_one_per_call(office):
    office.book("d1", "ann", 2)
    office.book("d1", "bob", 3)
    office.book("d1", "ann", 1)
    assert office.get_bookings("d1") == [("ann", 2), ("bob", 3), ("ann", 1)]
    assert office.get_bookings("h1") == []


@pytest.mark.parametrize("customer", BAD_CUSTOMERS)
def test_invalid_customers_are_rejected(office, customer):
    before = state(office)
    with pytest.raises(ValueError):
        office.book("d1", customer, 1)
    assert state(office) == before


@pytest.mark.parametrize("seats", BAD_SEATS)
def test_invalid_seat_counts_are_rejected_for_bookings(office, seats):
    before = state(office)
    with pytest.raises(ValueError):
        office.book("d1", "ann", seats)
    assert state(office) == before


# --- error order ------------------------------------------------------------


def test_a_used_showing_id_is_reported_before_an_unknown_title(office):
    with pytest.raises(BookingError):
        office.add_showing("d1", "Alien", 600, 5)


def test_an_unknown_title_is_reported_before_a_bad_start(office):
    with pytest.raises(KeyError):
        office.add_showing("d2", "Alien", -1, 0)


def test_a_bad_start_is_reported_before_bad_seats(office):
    with pytest.raises(ValueError):
        office.add_showing("d2", "Dune", -1, 0)
    assert office.get_showings("Dune") == ["d1"]


def test_an_unknown_showing_is_reported_before_a_bad_customer(office):
    with pytest.raises(KeyError):
        office.book("x9", "", 0)


def test_a_bad_customer_is_reported_before_bad_seats(office):
    with pytest.raises(ValueError):
        office.book("d1", "", 0)
    assert office.get_bookings("d1") == []


def test_bad_seats_are_reported_before_no_seats(office):
    # h1 has 4 seats, so 2.5 and 0 would also not be bookable.
    office.book("h1", "ann", 4)
    with pytest.raises(ValueError):
        office.book("h1", "bob", 2.5)
    with pytest.raises(ValueError):
        office.book("h1", "bob", 0)


def test_no_seats_is_a_booking_error():
    assert issubclass(NoSeats, BookingError)


def test_box_offices_do_not_share_data():
    first, second = BoxOffice(), BoxOffice()
    first.add_movie("Dune")
    first.add_showing("d1", "Dune", 600, 5)
    assert second.get_movies() == []
    second.add_movie("Dune")
    assert second.get_showings("Dune") == []
    with pytest.raises(KeyError):
        second.get_free_seats("d1")
