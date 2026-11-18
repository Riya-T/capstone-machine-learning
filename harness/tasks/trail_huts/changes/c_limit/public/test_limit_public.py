"""Public checks for the trail limit change. Shown to the editor, never to
the writer.

Usage (with trails.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/public/test_limit_public.py
"""

import pytest
from trails import TooManyTrails, TrailMap


@pytest.fixture
def trails():
    t = TrailMap()
    t.add_hut("Alpe", max_trails=1)
    t.add_hut("Berg")
    t.add_hut("Col")
    return t


def test_a_hut_takes_trails_up_to_its_limit(trails):
    assert trails.get_max_trails("Alpe") == 1
    assert trails.get_max_trails("Berg") is None
    trails.add_trail("Alpe", "Berg")
    with pytest.raises(TooManyTrails):
        trails.add_trail("Col", "Alpe")
    assert trails.get_neighbors("Alpe") == ["Berg"]
    assert trails.get_neighbors("Col") == []


def test_a_merge_that_would_go_over_the_limit_changes_nothing(trails):
    trails.add_trail("Berg", "Alpe")
    trails.add_hut("Dent")
    trails.add_trail("Dent", "Col")
    with pytest.raises(TooManyTrails):
        trails.merge_huts("Col", "Alpe")
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent"]
    assert trails.get_neighbors("Col") == ["Dent"]
    assert trails.get_neighbors("Alpe") == ["Berg"]
