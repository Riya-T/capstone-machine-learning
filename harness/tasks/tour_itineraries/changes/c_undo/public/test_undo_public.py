"""Public checks for the c_undo change (undo). Shown to the editor, never to
the writer.

Usage (with tours.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_undo_public.py
"""

import pytest
from tours import TourError, TourPlanner


@pytest.fixture
def planner():
    p = TourPlanner()
    p.add_tour("coast")
    p.add_tour("alps")
    return p


def test_undo_takes_back_the_last_added_city(planner):
    planner.add_city("coast", "lisbon")
    planner.add_city("coast", "porto")
    planner.undo()
    assert planner.get_cities("coast") == ["lisbon"]
    planner.undo()
    assert planner.get_cities("coast") == []


def test_undo_takes_back_a_removal(planner):
    planner.add_city("coast", "lisbon")
    planner.add_city("coast", "porto")
    planner.remove_city("coast", "lisbon")
    planner.undo()
    assert planner.get_cities("coast") == ["lisbon", "porto"]


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(TourError):
        TourPlanner().undo()
