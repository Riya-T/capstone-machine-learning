"""Hidden tests for the guest lookup change. Never shown to the writer or
the editor.

Usage (with seating.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lookup/private/test_lookup_new.py
"""

import pytest
from seating import SeatingChart


@pytest.fixture
def chart():
    c = SeatingChart()
    for name in ["rose", "lily", "iris"]:
        c.add_table(name)
    for guest in ["Ann", "Bob", "Cy"]:
        c.seat(guest, "rose")
    c.seat("Dee", "lily")
    c.seat("Eve", "lily")
    return c


def state(c):
    return [(t, c.get_guests(t)) for t in c.get_tables()]


def places(c):
    """Every seated guest with their table and seat, from the lookups."""
    return {g: (c.get_table_of(g), c.get_seat_number(g)) for t in c.get_tables() for g in c.get_guests(t)}


def test_every_guest_is_found_at_their_table_and_seat(chart):
    assert places(chart) == {
        "Ann": ("rose", 1),
        "Bob": ("rose", 2),
        "Cy": ("rose", 3),
        "Dee": ("lily", 1),
        "Eve": ("lily", 2),
    }


def test_a_newly_seated_guest_takes_the_next_seat(chart):
    chart.seat("Fay", "lily")
    chart.seat("Gus", "iris")
    assert chart.get_table_of("Fay") == "lily"
    assert chart.get_seat_number("Fay") == 3
    assert chart.get_seat_number("Gus") == 1


def test_guests_after_an_unseated_guest_move_up(chart):
    chart.unseat("Ann")
    assert chart.get_seat_number("Bob") == 1
    assert chart.get_seat_number("Cy") == 2
    with pytest.raises(KeyError):
        chart.get_table_of("Ann")
    with pytest.raises(KeyError):
        chart.get_seat_number("Ann")


def test_a_moved_guest_is_found_at_the_new_table(chart):
    chart.move_guest("Bob", "lily")
    assert chart.get_table_of("Bob") == "lily"
    assert chart.get_seat_number("Bob") == 3
    assert chart.get_seat_number("Cy") == 2
    assert chart.get_seat_number("Ann") == 1


def test_merged_guests_are_found_at_the_table_they_went_to(chart):
    chart.merge_tables("lily", "rose")
    assert chart.get_table_of("Dee") == "rose"
    assert chart.get_seat_number("Dee") == 4
    assert chart.get_table_of("Eve") == "rose"
    assert chart.get_seat_number("Eve") == 5
    assert chart.get_seat_number("Ann") == 1


def test_cleared_guests_are_not_found(chart):
    chart.clear_table("rose")
    for guest in ["Ann", "Bob", "Cy"]:
        with pytest.raises(KeyError):
            chart.get_table_of(guest)
        with pytest.raises(KeyError):
            chart.get_seat_number(guest)
    assert chart.get_table_of("Eve") == "lily"


def test_an_unseated_guest_seated_again_is_found_at_the_new_place(chart):
    chart.unseat("Ann")
    chart.seat("Ann", "lily")
    assert chart.get_table_of("Ann") == "lily"
    assert chart.get_seat_number("Ann") == 3
    assert chart.get_seat_number("Bob") == 1


def test_a_guest_who_was_never_seated_is_not_found(chart):
    with pytest.raises(KeyError):
        chart.get_table_of("Zed")
    with pytest.raises(KeyError):
        chart.get_seat_number("Zed")


def test_lookups_change_nothing(chart):
    before = state(chart)
    places(chart)
    with pytest.raises(KeyError):
        chart.get_table_of("Zed")
    assert state(chart) == before
    chart.seat("Fay", "rose")
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy", "Fay"]


def test_lookups_follow_a_longer_run_of_changes(chart):
    chart.move_guest("Ann", "iris")
    chart.unseat("Dee")
    chart.seat("Fay", "lily")
    chart.merge_tables("iris", "lily")
    chart.move_guest("Bob", "lily")
    assert places(chart) == {
        "Cy": ("rose", 1),
        "Eve": ("lily", 1),
        "Fay": ("lily", 2),
        "Ann": ("lily", 3),
        "Bob": ("lily", 4),
    }
