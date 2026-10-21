"""Public checks for the c_fill_percent change (adjustable fill rule). Shown
to the editor, never to the writer.

Usage (with seats.py importable, e.g. in the sandbox):
    python -m pytest changes/c_fill_percent/public/test_fill_percent_public.py
"""

import pytest
from seats import SeatPlanner


def test_fill_percent_for_the_whole_planner():
    p = SeatPlanner(fill_percent=100)
    p.add_coach("A", 10)
    assert p.get_fill_percent("A") == 100
    assert p.get_available("A") == 10
    assert p.reserve("smith", 10) == "A"


def test_fill_percent_for_one_coach():
    p = SeatPlanner()
    p.add_coach("A", 10, fill_percent=50)
    p.add_coach("B", 20)
    assert p.get_available("A") == 5
    assert p.get_available("B") == 14
    assert p.reserve("smith", 6) == "B"


def test_fill_percent_must_be_between_1_and_100():
    with pytest.raises(ValueError):
        SeatPlanner(fill_percent=0)
    p = SeatPlanner()
    with pytest.raises(ValueError):
        p.add_coach("A", 10, fill_percent=101)
    assert p.get_coaches() == []
