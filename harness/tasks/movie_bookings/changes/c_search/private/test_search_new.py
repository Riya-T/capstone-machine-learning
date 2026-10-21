"""Hidden tests for the c_search change (finding showings and bookings).
Never shown to the writer or the editor.

Usage (with bookings.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/private/test_search_new.py
"""

import pytest
from bookings import BoxOffice

BAD_TIMES = [-1, 2.5, "600", True]


@pytest.fixture
def office():
    bo = BoxOffice()
    bo.add_movie("Dune")
    bo.add_movie("Heat")
    bo.add_movie("Alien")
    bo.add_showing("d1", "Dune", 600, 10)
    bo.add_showing("h1", "Heat", 540, 4)
    bo.add_showing("d2", "Dune", 1200, 10)
    bo.add_showing("h2", "Heat", 600, 6)
    bo.add_showing("d3", "Dune", 540, 10)
    return bo


def test_without_filters_every_showing_is_found_earliest_first(office):
    assert office.find_showings() == ["h1", "d3", "d1", "h2", "d2"]


def test_filtering_by_title_keeps_the_time_order(office):
    assert office.find_showings(title="Dune") == ["d3", "d1", "d2"]
    assert office.find_showings(title="Heat") == ["h1", "h2"]
    assert office.find_showings(title="Alien") == []


def test_time_bounds_are_inclusive(office):
    assert office.find_showings(earliest=600) == ["d1", "h2", "d2"]
    assert office.find_showings(latest=600) == ["h1", "d3", "d1", "h2"]
    assert office.find_showings(earliest=600, latest=600) == ["d1", "h2"]
    assert office.find_showings(earliest=601, latest=1199) == []


def test_all_filters_combine(office):
    assert office.find_showings(title="Dune", earliest=541, latest=1200) == ["d1", "d2"]
    assert office.find_showings(title="Heat", earliest=0, latest=599) == ["h1"]


def test_a_window_from_midnight_includes_a_midnight_showing(office):
    office.add_showing("a1", "Alien", 0, 5)
    assert office.find_showings(earliest=0, latest=0) == ["a1"]
    assert office.find_showings(title="Alien") == ["a1"]


def test_finding_adds_nothing(office):
    office.find_showings(title="Dune", earliest=0)
    assert office.get_showings("Dune") == ["d3", "d1", "d2"]
    assert office.get_free_seats("d1") == 10


@pytest.mark.parametrize("title", ["Up", 2])
def test_find_showings_with_an_unknown_title_raises_key_error(office, title):
    with pytest.raises(KeyError):
        office.find_showings(title=title)


@pytest.mark.parametrize("time", BAD_TIMES)
def test_find_showings_rejects_bad_times(office, time):
    with pytest.raises(ValueError):
        office.find_showings(earliest=time)
    with pytest.raises(ValueError):
        office.find_showings(latest=time)


def test_find_showings_rejects_a_window_that_ends_before_it_starts(office):
    with pytest.raises(ValueError):
        office.find_showings(earliest=601, latest=600)


def test_an_unknown_title_is_reported_before_bad_times_when_finding(office):
    with pytest.raises(KeyError):
        office.find_showings(title="Up", earliest=-1)
    with pytest.raises(KeyError):
        office.find_showings(title="Up", earliest=5, latest=1)


def test_a_bad_time_is_reported_before_a_reversed_window(office):
    with pytest.raises(ValueError):
        office.find_showings(earliest=5, latest=-1)


def test_customer_bookings_are_in_booking_order_across_showings(office):
    office.book("d2", "ann", 1)
    office.book("h1", "bob", 2)
    office.book("d1", "ann", 4)
    office.book("d2", "ann", 2)
    office.book("h1", "ann", 1)
    assert office.find_customer_bookings("ann") == [("d2", 1), ("d1", 4), ("d2", 2), ("h1", 1)]
    assert office.find_customer_bookings("bob") == [("h1", 2)]


def test_a_customer_without_bookings_has_an_empty_list(office):
    office.book("d1", "ann", 1)
    assert office.find_customer_bookings("cat") == []


@pytest.mark.parametrize("customer", ["", None, 4])
def test_find_customer_bookings_rejects_bad_customers(office, customer):
    with pytest.raises(ValueError):
        office.find_customer_bookings(customer)
