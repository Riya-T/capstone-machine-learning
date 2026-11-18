"""Public checks for trails.py.

Usage (with trails.py importable, e.g. in the sandbox):
    python -m pytest public/test_trails_public.py
"""

import pytest
from trails import TrailError, TrailMap


@pytest.fixture
def trails():
    t = TrailMap()
    for name in ["Alpe", "Berg", "Col", "Dent"]:
        t.add_hut(name)
    return t


def test_neighbors_are_listed_in_the_order_the_trails_were_added(trails):
    trails.add_trail("Alpe", "Col")
    trails.add_trail("Berg", "Alpe")
    trails.add_trail("Alpe", "Dent")
    assert trails.get_neighbors("Alpe") == ["Col", "Berg", "Dent"]
    assert trails.get_neighbors("Berg") == ["Alpe"]
    assert trails.get_neighbors("Col") == ["Alpe"]


def test_a_trail_that_exists_cannot_be_added_again(trails):
    trails.add_trail("Alpe", "Berg")
    with pytest.raises(TrailError):
        trails.add_trail("Berg", "Alpe")
    assert trails.get_neighbors("Alpe") == ["Berg"]


def test_removing_a_trail_keeps_the_others_in_order(trails):
    trails.add_trail("Alpe", "Berg")
    trails.add_trail("Alpe", "Col")
    trails.add_trail("Alpe", "Dent")
    trails.remove_trail("Col", "Alpe")
    assert trails.get_neighbors("Alpe") == ["Berg", "Dent"]
    assert trails.get_neighbors("Col") == []


def test_close_hut_removes_the_hut_and_its_trails(trails):
    trails.add_trail("Alpe", "Berg")
    trails.add_trail("Col", "Berg")
    trails.add_trail("Col", "Dent")
    assert trails.close_hut("Berg") == 2
    assert trails.get_huts() == ["Alpe", "Col", "Dent"]
    assert trails.get_neighbors("Alpe") == []
    assert trails.get_neighbors("Col") == ["Dent"]
    with pytest.raises(KeyError):
        trails.get_neighbors("Berg")


def test_merge_huts_hands_the_trails_over(trails):
    trails.add_trail("Alpe", "Berg")
    trails.add_trail("Alpe", "Dent")
    trails.add_trail("Berg", "Dent")
    trails.merge_huts("Alpe", "Col")
    assert trails.get_huts() == ["Berg", "Col", "Dent"]
    assert sorted(trails.get_neighbors("Col")) == ["Berg", "Dent"]
    assert trails.get_neighbors("Berg") == ["Dent", "Col"]
    assert trails.get_neighbors("Dent") == ["Berg", "Col"]
    with pytest.raises(KeyError):
        trails.get_neighbors("Alpe")


def test_huts_are_listed_in_the_order_added():
    t = TrailMap()
    for name in ["Col", "Alpe", "Berg"]:
        t.add_hut(name)
    assert t.get_huts() == ["Col", "Alpe", "Berg"]
