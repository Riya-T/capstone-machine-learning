"""Hidden tests for the undo change. Never shown to the writer or the
editor.

Usage (with seating.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_seat_undo_new.py
"""

import pytest
from seating import SeatingChart, SeatingError


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


# --- simple calls -------------------------------------------------------------


def test_undo_of_seat_frees_the_guest(chart):
    before = state(chart)
    chart.seat("Fay", "iris")
    chart.undo()
    assert state(chart) == before
    chart.seat("Fay", "lily")
    assert chart.get_guests("lily") == ["Dee", "Eve", "Fay"]


def test_undo_of_unseat_puts_the_guest_back_in_their_place(chart):
    before = state(chart)
    chart.unseat("Bob")
    chart.undo()
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy"]
    assert state(chart) == before


def test_undo_of_unseating_the_first_guest(chart):
    chart.unseat("Dee")
    chart.undo()
    assert chart.get_guests("lily") == ["Dee", "Eve"]


def test_a_guest_brought_back_by_undo_is_seated_again(chart):
    chart.unseat("Bob")
    chart.undo()
    with pytest.raises(SeatingError):
        chart.seat("Bob", "iris")
    chart.unseat("Bob")
    assert chart.get_guests("rose") == ["Ann", "Cy"]


def test_undo_of_move_guest_puts_the_guest_back_in_their_place(chart):
    before = state(chart)
    chart.move_guest("Bob", "lily")
    assert chart.get_guests("lily") == ["Dee", "Eve", "Bob"]
    chart.undo()
    assert state(chart) == before
    chart.move_guest("Bob", "iris")
    assert chart.get_guests("rose") == ["Ann", "Cy"]


# --- composite calls are undone as a whole ------------------------------------


def test_one_undo_takes_back_a_whole_clear_table(chart):
    before = state(chart)
    assert chart.clear_table("rose") == 3
    chart.undo()
    assert state(chart) == before
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy"]


def test_a_cleared_table_comes_back_in_its_place(chart):
    chart.add_table("aster")
    before = state(chart)
    assert chart.clear_table("lily") == 2
    assert chart.get_tables() == ["rose", "iris", "aster"]
    chart.undo()
    assert chart.get_tables() == ["rose", "lily", "iris", "aster"]
    assert chart.get_guests("lily") == ["Dee", "Eve"]
    assert state(chart) == before


def test_guests_brought_back_from_a_clear_are_seated_again(chart):
    chart.clear_table("lily")
    chart.undo()
    with pytest.raises(SeatingError):
        chart.seat("Eve", "iris")
    chart.move_guest("Dee", "rose")
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy", "Dee"]
    assert chart.get_guests("lily") == ["Eve"]


def test_one_undo_takes_back_a_whole_merge(chart):
    before = state(chart)
    assert chart.merge_tables("rose", "lily") == 3
    chart.undo()
    assert state(chart) == before
    assert chart.get_tables() == ["rose", "lily", "iris"]
    assert chart.get_guests("lily") == ["Dee", "Eve"]


def test_a_table_brought_back_keeps_its_place_in_the_list(chart):
    chart.add_table("aster")
    before = state(chart)
    chart.merge_tables("lily", "aster")
    assert chart.get_tables() == ["rose", "iris", "aster"]
    chart.undo()
    assert chart.get_tables() == ["rose", "lily", "iris", "aster"]
    assert state(chart) == before


def test_a_table_brought_back_is_in_use_again(chart):
    chart.merge_tables("lily", "iris")
    chart.undo()
    chart.seat("Fay", "lily")
    assert chart.get_guests("lily") == ["Dee", "Eve", "Fay"]
    with pytest.raises(SeatingError):
        chart.add_table("lily")
    chart.move_guest("Eve", "iris")
    assert chart.get_guests("iris") == ["Eve"]


def test_undo_of_merging_an_empty_table_brings_it_back(chart):
    assert chart.merge_tables("iris", "rose") == 0
    chart.undo()
    assert chart.get_tables() == ["rose", "lily", "iris"]
    assert chart.get_guests("iris") == []
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy"]


def test_undo_of_add_table_removes_it_and_frees_the_name(chart):
    chart.add_table("aster")
    chart.undo()
    assert chart.get_tables() == ["rose", "lily", "iris"]
    with pytest.raises(KeyError):
        chart.get_guests("aster")
    chart.add_table("aster")
    assert chart.get_tables() == ["rose", "lily", "iris", "aster"]


def test_undo_through_a_name_that_was_merged_and_added_again(chart):
    chart.add_table("aster")
    chart.seat("Fay", "aster")
    chart.merge_tables("aster", "iris")
    chart.add_table("aster")  # a new, empty aster
    chart.seat("Gus", "aster")
    chart.undo()  # Gus
    chart.undo()  # the new aster
    assert chart.get_tables() == ["rose", "lily", "iris"]
    chart.undo()  # the merge: the old aster comes back with Fay
    assert chart.get_tables() == ["rose", "lily", "iris", "aster"]
    assert chart.get_guests("aster") == ["Fay"]
    assert chart.get_guests("iris") == []
    chart.undo()  # Fay
    chart.undo()  # the first aster
    assert chart.get_tables() == ["rose", "lily", "iris"]


# --- what is and is not recorded ----------------------------------------------


def test_each_undo_goes_one_call_further_back():
    c = SeatingChart()
    calls = [
        lambda: c.add_table("rose"),
        lambda: c.add_table("lily"),
        lambda: c.seat("Ann", "rose"),
        lambda: c.seat("Bob", "rose"),
        lambda: c.seat("Cy", "rose"),
        lambda: c.add_table("iris"),
        lambda: c.seat("Dee", "lily"),
        lambda: c.move_guest("Bob", "lily"),
        lambda: c.unseat("Ann"),
        lambda: c.seat("Eve", "iris"),
        lambda: c.merge_tables("lily", "iris"),
        lambda: c.clear_table("rose"),
        lambda: c.add_table("aster"),
        lambda: c.seat("Fay", "aster"),
        lambda: c.move_guest("Dee", "aster"),
        lambda: c.merge_tables("iris", "aster"),
    ]
    states = [state(c)]
    for call in calls:
        call()
        states.append(state(c))
    assert state(c) == [("aster", ["Fay", "Dee", "Eve", "Bob"])]
    for expected in reversed(states[:-1]):
        c.undo()
        assert state(c) == expected
    with pytest.raises(SeatingError):
        c.undo()
    assert c.get_tables() == []


def test_failed_calls_are_not_recorded(chart):
    chart.seat("Fay", "iris")
    for call in (
        lambda: chart.seat("Ann", "iris"),
        lambda: chart.seat("Gus", "aster"),
        lambda: chart.unseat("Zed"),
        lambda: chart.move_guest("Ann", "rose"),
        lambda: chart.move_guest("Zed", "lily"),
        lambda: chart.merge_tables("rose", "rose"),
        lambda: chart.merge_tables("rose", "aster"),
        lambda: chart.clear_table("aster"),
        lambda: chart.add_table("rose"),
    ):
        with pytest.raises((ValueError, KeyError, SeatingError)):
            call()
    chart.undo()  # Fay
    assert chart.get_guests("iris") == []
    chart.undo()  # Eve
    assert chart.get_guests("lily") == ["Dee"]
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy"]


def test_get_calls_are_not_recorded(chart):
    chart.seat("Fay", "iris")
    chart.get_guests("iris")
    chart.get_tables()
    chart.undo()
    assert chart.get_guests("iris") == []
    assert chart.get_guests("lily") == ["Dee", "Eve"]


def test_there_is_no_redo():
    c = SeatingChart()
    c.add_table("rose")
    c.seat("Ann", "rose")
    c.undo()
    c.undo()
    assert c.get_tables() == []
    with pytest.raises(SeatingError):
        c.undo()


def test_a_new_call_after_an_undo_is_undone_first(chart):
    chart.seat("Fay", "iris")
    chart.undo()
    chart.seat("Gus", "iris")
    chart.undo()
    assert chart.get_guests("iris") == []
    chart.undo()  # Eve from the fixture
    assert chart.get_guests("lily") == ["Dee"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    c = SeatingChart()
    with pytest.raises(SeatingError):
        c.undo()
    c.add_table("rose")
    c.undo()
    with pytest.raises(SeatingError):
        c.undo()
    assert c.get_tables() == []
    c.add_table("rose")
    c.seat("Ann", "rose")
    assert c.get_guests("rose") == ["Ann"]


def test_the_whole_fixture_can_be_undone(chart):
    for _ in range(8):
        chart.undo()
    assert chart.get_tables() == []
    with pytest.raises(SeatingError):
        chart.undo()
