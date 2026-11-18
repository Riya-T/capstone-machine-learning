"""Public checks for the undo change. Shown to the editor, never to the
writer.

Usage (with trails.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/public/test_trail_undo_public.py
"""

import pytest
from trails import TrailError, TrailMap


@pytest.fixture
def trails():
    t = TrailMap()
    for name in ["Alpe", "Berg", "Col"]:
        t.add_hut(name)
    return t


def test_undo_takes_back_the_last_trail_added(trails):
    trails.add_trail("Alpe", "Berg")
    trails.add_trail("Alpe", "Col")
    trails.undo()
    assert trails.get_neighbors("Alpe") == ["Berg"]
    assert trails.get_neighbors("Col") == []
    trails.undo()
    assert trails.get_neighbors("Alpe") == []


def test_undo_takes_back_a_removed_trail(trails):
    trails.add_trail("Alpe", "Berg")
    trails.remove_trail("Berg", "Alpe")
    trails.undo()
    assert trails.get_neighbors("Alpe") == ["Berg"]
    assert trails.get_neighbors("Berg") == ["Alpe"]


def test_undo_with_nothing_to_undo_raises():
    with pytest.raises(TrailError):
        TrailMap().undo()
