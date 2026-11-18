"""Public checks for the route change. Shown to the editor, never to the
writer.

Usage (with trails.py importable, e.g. in the sandbox):
    python -m pytest changes/c_route/public/test_route_public.py
"""

import pytest
from trails import TrailError, TrailMap


@pytest.fixture
def trails():
    t = TrailMap()
    for name in ["Alpe", "Berg", "Col", "Dent"]:
        t.add_hut(name)
    return t


def test_add_route_joins_each_hut_to_the_next(trails):
    trails.add_route(["Alpe", "Berg", "Col"])
    assert trails.get_neighbors("Alpe") == ["Berg"]
    assert trails.get_neighbors("Berg") == ["Alpe", "Col"]
    assert trails.get_neighbors("Col") == ["Berg"]


def test_a_route_with_a_trail_that_exists_adds_nothing(trails):
    trails.add_trail("Col", "Dent")
    with pytest.raises(TrailError):
        trails.add_route(["Alpe", "Berg", "Col", "Dent"])
    assert trails.get_neighbors("Berg") == []
    assert trails.get_neighbors("Col") == ["Dent"]
