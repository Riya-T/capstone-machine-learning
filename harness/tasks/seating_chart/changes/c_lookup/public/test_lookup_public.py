"""Public checks for the guest lookup change. Shown to the editor, never to
the writer.

Usage (with seating.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lookup/public/test_lookup_public.py
"""

import pytest
from seating import SeatingChart


@pytest.fixture
def chart():
    c = SeatingChart()
    c.add_table("rose")
    c.add_table("lily")
    for guest in ["Ann", "Bob", "Cy"]:
        c.seat(guest, "rose")
    return c


def test_a_guest_is_found_at_their_table_and_seat(chart):
    assert chart.get_table_of("Bob") == "rose"
    assert chart.get_seat_number("Ann") == 1
    assert chart.get_seat_number("Cy") == 3


def test_a_guest_who_is_not_seated_is_not_found(chart):
    with pytest.raises(KeyError):
        chart.get_table_of("Zed")
    with pytest.raises(KeyError):
        chart.get_seat_number("Zed")
