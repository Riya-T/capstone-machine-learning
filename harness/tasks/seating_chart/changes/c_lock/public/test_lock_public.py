"""Public checks for the table lock change. Shown to the editor, never to
the writer.

Usage (with seating.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lock/public/test_lock_public.py
"""

import pytest
from seating import SeatingChart, TableLocked


@pytest.fixture
def chart():
    c = SeatingChart()
    c.add_table("rose")
    c.add_table("lily")
    c.seat("Ann", "rose")
    return c


def test_nobody_can_be_seated_at_a_locked_table(chart):
    assert chart.get_locked_tables() == []
    chart.lock_table("rose")
    assert chart.get_locked_tables() == ["rose"]
    with pytest.raises(TableLocked):
        chart.seat("Bob", "rose")
    assert chart.get_guests("rose") == ["Ann"]
    chart.unlock_table("rose")
    chart.seat("Bob", "rose")
    assert chart.get_guests("rose") == ["Ann", "Bob"]


def test_a_guest_cannot_move_away_from_a_locked_table(chart):
    chart.lock_table("rose")
    with pytest.raises(TableLocked):
        chart.move_guest("Ann", "lily")
    assert chart.get_guests("rose") == ["Ann"]
    assert chart.get_guests("lily") == []
