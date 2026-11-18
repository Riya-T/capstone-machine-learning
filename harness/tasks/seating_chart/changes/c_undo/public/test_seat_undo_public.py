"""Public checks for the undo change. Shown to the editor, never to the
writer.

Usage (with seating.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_seat_undo_public.py
"""

import pytest
from seating import SeatingChart, SeatingError


@pytest.fixture
def chart():
    c = SeatingChart()
    c.add_table("rose")
    c.add_table("lily")
    return c


def test_undo_takes_back_the_last_guest_seated(chart):
    chart.seat("Ann", "rose")
    chart.seat("Bob", "rose")
    chart.undo()
    assert chart.get_guests("rose") == ["Ann"]
    chart.undo()
    assert chart.get_guests("rose") == []


def test_undo_takes_back_a_move(chart):
    chart.seat("Ann", "rose")
    chart.move_guest("Ann", "lily")
    chart.undo()
    assert chart.get_guests("rose") == ["Ann"]
    assert chart.get_guests("lily") == []


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(SeatingError):
        SeatingChart().undo()
