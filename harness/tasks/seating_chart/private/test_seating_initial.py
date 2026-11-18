"""Hidden tests for the initial seating_chart spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with seating.py importable, e.g. in the sandbox):
    python -m pytest private/test_seating_initial.py
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
    return c


def state(c):
    """Every table in order with its guests in order, to check that a failed
    call changed nothing."""
    return [(t, c.get_guests(t)) for t in c.get_tables()]


# --- tables -----------------------------------------------------------------


def test_a_new_table_is_empty():
    c = SeatingChart()
    c.add_table("rose")
    assert c.get_guests("rose") == []


def test_tables_keep_the_order_they_were_added_in():
    c = SeatingChart()
    for name in ["lily", "rose", "iris", "aster"]:
        c.add_table(name)
    assert c.get_tables() == ["lily", "rose", "iris", "aster"]


def test_a_table_name_in_use_cannot_be_added_again(chart):
    before = state(chart)
    with pytest.raises(SeatingError):
        chart.add_table("rose")
    assert state(chart) == before


def test_a_merged_name_can_be_added_again_as_a_new_empty_table(chart):
    chart.merge_tables("rose", "iris")
    chart.add_table("rose")
    assert chart.get_tables() == ["lily", "iris", "rose"]
    assert chart.get_guests("rose") == []
    assert chart.get_guests("iris") == ["Ann", "Bob", "Cy"]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.seat("Eve", "aster"),
        lambda c: c.move_guest("Ann", "aster"),
        lambda c: c.merge_tables("aster", "rose"),
        lambda c: c.merge_tables("rose", "aster"),
        lambda c: c.clear_table("aster"),
        lambda c: c.get_guests("aster"),
    ],
)
def test_tables_never_added_raise_key_error(chart, call):
    before = state(chart)
    with pytest.raises(KeyError):
        call(chart)
    assert state(chart) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.seat("Eve", "lily"),
        lambda c: c.move_guest("Ann", "lily"),
        lambda c: c.merge_tables("lily", "rose"),
        lambda c: c.merge_tables("rose", "lily"),
        lambda c: c.clear_table("lily"),
        lambda c: c.get_guests("lily"),
    ],
)
def test_a_merged_table_is_not_in_use(chart, call):
    chart.merge_tables("lily", "iris")
    before = state(chart)
    with pytest.raises(KeyError):
        call(chart)
    assert state(chart) == before


# --- seating and unseating ------------------------------------------------------


def test_seat_puts_a_guest_after_the_ones_already_there(chart):
    chart.seat("Eve", "lily")
    chart.seat("Fay", "rose")
    assert chart.get_guests("lily") == ["Dee", "Eve"]
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy", "Fay"]


def test_a_seated_guest_cannot_be_seated_again(chart):
    before = state(chart)
    with pytest.raises(SeatingError):
        chart.seat("Bob", "iris")
    with pytest.raises(SeatingError):
        chart.seat("Bob", "rose")
    assert state(chart) == before


def test_unseat_takes_a_guest_off_and_keeps_the_others_in_order(chart):
    chart.unseat("Bob")
    assert chart.get_guests("rose") == ["Ann", "Cy"]
    chart.seat("Bob", "rose")
    assert chart.get_guests("rose") == ["Ann", "Cy", "Bob"]


def test_unseating_a_guest_who_is_not_seated_raises_key_error(chart):
    chart.unseat("Dee")
    before = state(chart)
    with pytest.raises(KeyError):
        chart.unseat("Zed")
    with pytest.raises(KeyError):
        chart.unseat("Dee")
    assert state(chart) == before


# --- moving -----------------------------------------------------------------


def test_move_guest_puts_the_guest_at_the_end_of_the_new_table(chart):
    chart.move_guest("Ann", "lily")
    assert chart.get_guests("rose") == ["Bob", "Cy"]
    assert chart.get_guests("lily") == ["Dee", "Ann"]
    chart.move_guest("Ann", "rose")
    assert chart.get_guests("rose") == ["Bob", "Cy", "Ann"]


def test_moving_a_guest_who_is_not_seated_raises_key_error(chart):
    before = state(chart)
    with pytest.raises(KeyError):
        chart.move_guest("Zed", "iris")
    assert state(chart) == before


def test_moving_a_guest_to_their_own_table_raises_value_error(chart):
    before = state(chart)
    with pytest.raises(ValueError):
        chart.move_guest("Bob", "rose")
    assert state(chart) == before


# --- merging ----------------------------------------------------------------


def test_merge_tables_puts_the_guests_after_the_ones_already_there(chart):
    assert chart.merge_tables("rose", "lily") == 3
    assert chart.get_tables() == ["lily", "iris"]
    assert chart.get_guests("lily") == ["Dee", "Ann", "Bob", "Cy"]


def test_merging_an_empty_table_removes_it(chart):
    assert chart.merge_tables("iris", "rose") == 0
    assert chart.get_tables() == ["rose", "lily"]
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy"]


def test_the_other_tables_keep_their_order_after_a_merge(chart):
    chart.add_table("aster")
    chart.merge_tables("lily", "aster")
    assert chart.get_tables() == ["rose", "iris", "aster"]


def test_merged_guests_are_still_seated_at_their_new_table(chart):
    chart.merge_tables("rose", "iris")
    with pytest.raises(SeatingError):
        chart.seat("Ann", "lily")
    chart.move_guest("Bob", "lily")
    chart.unseat("Ann")
    assert chart.get_guests("iris") == ["Cy"]
    assert chart.get_guests("lily") == ["Dee", "Bob"]


def test_merging_a_table_into_itself_raises_value_error(chart):
    before = state(chart)
    with pytest.raises(ValueError):
        chart.merge_tables("rose", "rose")
    assert state(chart) == before


# --- clearing ---------------------------------------------------------------


def test_clear_table_removes_the_table_and_returns_how_many_guests(chart):
    assert chart.clear_table("rose") == 3
    assert state(chart) == [("lily", ["Dee"]), ("iris", [])]


def test_clearing_an_empty_table_removes_it(chart):
    assert chart.clear_table("iris") == 0
    assert state(chart) == [("rose", ["Ann", "Bob", "Cy"]), ("lily", ["Dee"])]


def test_the_other_tables_keep_their_order_after_a_clear(chart):
    chart.add_table("aster")
    chart.clear_table("lily")
    assert chart.get_tables() == ["rose", "iris", "aster"]
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy"]


def test_a_cleared_name_can_be_added_again_as_a_new_empty_table(chart):
    chart.clear_table("rose")
    chart.add_table("rose")
    assert chart.get_tables() == ["lily", "iris", "rose"]
    assert chart.get_guests("rose") == []


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.seat("Eve", "iris"),
        lambda c: c.move_guest("Ann", "iris"),
        lambda c: c.merge_tables("iris", "rose"),
        lambda c: c.merge_tables("rose", "iris"),
        lambda c: c.clear_table("iris"),
        lambda c: c.get_guests("iris"),
    ],
)
def test_a_cleared_table_is_not_in_use(chart, call):
    chart.clear_table("iris")
    before = state(chart)
    with pytest.raises(KeyError):
        call(chart)
    assert state(chart) == before


# --- general ----------------------------------------------------------------


def test_charts_do_not_share_tables_or_guests():
    first, second = SeatingChart(), SeatingChart()
    first.add_table("rose")
    first.seat("Ann", "rose")
    assert second.get_tables() == []
    second.add_table("rose")
    second.seat("Ann", "rose")
    assert second.get_guests("rose") == ["Ann"]
