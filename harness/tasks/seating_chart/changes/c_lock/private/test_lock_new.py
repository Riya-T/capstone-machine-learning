"""Hidden tests for the table lock change. Never shown to the writer or the
editor.

Usage (with seating.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/private/test_lock_new.py
"""

import pytest
from seating import SeatingChart, SeatingError, TableLocked


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
    return [(t, c.get_guests(t)) for t in c.get_tables()]


# --- locking ----------------------------------------------------------------------


def test_no_table_starts_locked(chart):
    assert chart.get_locked_tables() == []
    chart.add_table("aster")
    assert chart.get_locked_tables() == []


def test_locked_tables_are_listed_in_table_order(chart):
    chart.lock_table("iris")
    chart.lock_table("rose")
    assert chart.get_locked_tables() == ["rose", "iris"]
    chart.unlock_table("rose")
    assert chart.get_locked_tables() == ["iris"]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.lock_table("aster"),
        lambda c: c.unlock_table("aster"),
        lambda c: c.lock_table("lily"),  # merged below
        lambda c: c.unlock_table("lily"),
    ],
)
def test_lock_and_unlock_of_a_table_not_in_use_raise_key_error(chart, call):
    chart.merge_tables("lily", "iris")
    with pytest.raises(KeyError):
        call(chart)


def test_locking_changes_no_guests(chart):
    before = state(chart)
    chart.lock_table("rose")
    chart.lock_table("iris")
    assert state(chart) == before


def test_table_locked_is_a_seating_error():
    assert issubclass(TableLocked, SeatingError)


# --- what a lock refuses ----------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.seat("Eve", "rose"),
        lambda c: c.unseat("Bob"),
        lambda c: c.move_guest("Bob", "iris"),
        lambda c: c.move_guest("Dee", "rose"),
        lambda c: c.merge_tables("rose", "iris"),
        lambda c: c.merge_tables("lily", "rose"),
        lambda c: c.clear_table("rose"),
    ],
    ids=["seat", "unseat", "move_from", "move_to", "merge_from", "merge_into", "clear"],
)
def test_calls_involving_a_locked_table_raise_and_change_nothing(chart, call):
    chart.lock_table("rose")
    before = state(chart)
    with pytest.raises(TableLocked):
        call(chart)
    assert state(chart) == before
    assert chart.get_tables() == ["rose", "lily", "iris"]


def test_a_refused_merge_keeps_both_tables(chart):
    chart.lock_table("iris")
    with pytest.raises(TableLocked):
        chart.merge_tables("lily", "iris")
    assert chart.get_tables() == ["rose", "lily", "iris"]
    assert chart.get_guests("lily") == ["Dee"]


def test_merging_an_empty_locked_table_is_refused(chart):
    chart.lock_table("iris")
    with pytest.raises(TableLocked):
        chart.merge_tables("iris", "lily")
    assert chart.get_tables() == ["rose", "lily", "iris"]


# --- what still works -------------------------------------------------------------


def test_other_tables_work_while_one_is_locked(chart):
    chart.lock_table("rose")
    chart.seat("Eve", "lily")
    chart.move_guest("Dee", "iris")
    chart.unseat("Eve")
    assert chart.merge_tables("iris", "lily") == 1
    chart.add_table("aster")
    assert chart.clear_table("lily") == 1
    assert state(chart) == [("rose", ["Ann", "Bob", "Cy"]), ("aster", [])]
    assert chart.get_locked_tables() == ["rose"]


def test_unlock_lifts_the_lock(chart):
    chart.lock_table("rose")
    chart.unlock_table("rose")
    chart.move_guest("Bob", "lily")
    assert chart.clear_table("rose") == 2
    assert chart.get_guests("lily") == ["Dee", "Bob"]


def test_a_merged_table_name_added_again_is_not_locked(chart):
    chart.merge_tables("lily", "iris")
    chart.add_table("lily")
    assert chart.get_locked_tables() == []
    chart.seat("Eve", "lily")
    assert chart.get_guests("lily") == ["Eve"]


# --- undo -------------------------------------------------------------------------


def test_undo_of_lock_table_unlocks_it(chart):
    chart.lock_table("rose")
    chart.undo()
    assert chart.get_locked_tables() == []
    chart.seat("Eve", "rose")
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy", "Eve"]


def test_undo_of_unlock_table_locks_it_again(chart):
    chart.lock_table("lily")
    chart.unlock_table("lily")
    chart.undo()
    assert chart.get_locked_tables() == ["lily"]
    with pytest.raises(TableLocked):
        chart.seat("Eve", "lily")


def test_undo_goes_back_through_a_lock_to_earlier_calls(chart):
    chart.seat("Eve", "iris")
    chart.lock_table("iris")
    chart.undo()  # the lock
    chart.undo()  # Eve
    assert chart.get_guests("iris") == []
    assert chart.get_locked_tables() == []


def test_a_refused_call_is_not_undone(chart):
    chart.seat("Eve", "iris")
    chart.lock_table("rose")
    with pytest.raises(TableLocked):
        chart.seat("Fay", "rose")
    chart.undo()  # the lock
    assert chart.get_locked_tables() == []
    assert chart.get_guests("rose") == ["Ann", "Bob", "Cy"]
    chart.undo()  # Eve
    assert chart.get_guests("iris") == []
