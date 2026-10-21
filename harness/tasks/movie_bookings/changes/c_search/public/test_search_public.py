"""Public checks for the c_search change (finding showings and bookings).
Shown to the editor, never to the writer.

Usage (with bookings.py importable, e.g. in the sandbox):
    python -m pytest changes/c_search/public/test_search_public.py
"""

import pytest
from bookings import BoxOffice


@pytest.fixture
def office():
    bo = BoxOffice()
    bo.add_movie("Dune")
    bo.add_movie("Heat")
    bo.add_showing("d1", "Dune", 600, 10)
    bo.add_showing("h1", "Heat", 540, 4)
    bo.add_showing("d2", "Dune", 1200, 10)
    return bo


def test_showings_can_be_found_by_time_window(office):
    assert office.find_showings(earliest=540, latest=600) == ["h1", "d1"]
    assert office.find_showings(title="Dune", latest=700) == ["d1"]
    assert office.find_showings() == ["h1", "d1", "d2"]


def test_a_customers_bookings_span_showings(office):
    office.book("d1", "ann", 2)
    office.book("h1", "bob", 1)
    office.book("h1", "ann", 3)
    assert office.find_customer_bookings("ann") == [("d1", 2), ("h1", 3)]
    assert office.find_customer_bookings("cat") == []
