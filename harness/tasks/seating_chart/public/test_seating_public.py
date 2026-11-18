"""Public checks for seating.py.

Usage (with seating.py importable, e.g. in the sandbox):
    python -m pytest public/test_seating_public.py
"""

import pytest
from seating import SeatingChart, SeatingError


@pytest.fixture
def chart():
    c = SeatingChart()
    c.add_table("rose")
    c.add_table("lily")
    return c


def test_guests_are_listed_in_seating_order(chart):
    chart.seat("Ann", "rose")
    chart.seat("Bob", "rose")
    chart.seat("Cy", "rose")
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy"]
    assert chart.get_guests("lily") == []


def test_a_guest_cannot_be_seated_twice(chart):
    chart.seat("Ann", "rose")
    with pytest.raises(SeatingError):
        chart.seat("Ann", "lily")
    assert chart.get_guests("rose") == ["Ann"]
    assert chart.get_guests("lily") == []


def test_unseat_and_move_keep_the_others_in_order(chart):
    for guest in ["Ann", "Bob", "Cy", "Dee"]:
        chart.seat(guest, "rose")
    chart.unseat("Bob")
    chart.move_guest("Ann", "lily")
    assert chart.get_guests("rose") == ["Cy", "Dee"]
    assert chart.get_guests("lily") == ["Ann"]


def test_merge_tables_moves_the_guests_and_removes_the_table(chart):
    chart.seat("Ann", "rose")
    chart.seat("Bob", "rose")
    assert chart.merge_tables("rose", "lily") == 2
    assert chart.get_tables() == ["lily"]
    assert chart.get_guests("lily") == ["Ann", "Bob"]
    with pytest.raises(KeyError):
        chart.get_guests("rose")
    with pytest.raises(KeyError):
        chart.seat("Cy", "rose")


def test_clear_table_removes_the_table_with_its_guests(chart):
    chart.seat("Ann", "rose")
    chart.seat("Bob", "rose")
    chart.seat("Cy", "lily")
    assert chart.clear_table("rose") == 2
    assert chart.get_tables() == ["lily"]
    assert chart.get_guests("lily") == ["Cy"]
    with pytest.raises(KeyError):
        chart.get_guests("rose")


def test_tables_are_listed_in_the_order_added():
    c = SeatingChart()
    for name in ["rose", "iris", "lily"]:
        c.add_table(name)
    assert c.get_tables() == ["rose", "iris", "lily"]
