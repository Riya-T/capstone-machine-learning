"""Hidden tests for the route change. Never shown to the writer or the
editor.

Usage (with trails.py importable, e.g. in the sandbox):
    python -m pytest changes/c_route/private/test_route_new.py
"""

import pytest
from trails import TrailError, TrailMap


@pytest.fixture
def trails():
    # Alpe-Berg and Col-Dent; Eck has no trails.
    t = TrailMap()
    for name in ["Alpe", "Berg", "Col", "Dent", "Eck"]:
        t.add_hut(name)
    t.add_trail("Alpe", "Berg")
    t.add_trail("Col", "Dent")
    return t


def state(t):
    return [(h, t.get_neighbors(h)) for h in t.get_huts()]


# --- successful routes ------------------------------------------------------------


def test_a_route_of_two_huts_adds_one_trail(trails):
    trails.add_route(["Eck", "Alpe"])
    assert trails.get_neighbors("Eck") == ["Alpe"]
    assert trails.get_neighbors("Alpe") == ["Berg", "Eck"]


def test_a_longer_route_adds_its_trails_in_order(trails):
    trails.add_route(["Berg", "Eck", "Dent", "Alpe"])
    assert state(trails) == [
        ("Alpe", ["Berg", "Dent"]),
        ("Berg", ["Alpe", "Eck"]),
        ("Col", ["Dent"]),
        ("Dent", ["Col", "Eck", "Alpe"]),
        ("Eck", ["Berg", "Dent"]),
    ]


def test_a_route_may_come_back_to_a_hut(trails):
    trails.add_route(["Alpe", "Col", "Eck", "Alpe"])
    assert trails.get_neighbors("Alpe") == ["Berg", "Col", "Eck"]
    assert trails.get_neighbors("Eck") == ["Col", "Alpe"]
    assert trails.get_neighbors("Col") == ["Dent", "Alpe", "Eck"]


def test_a_route_gives_the_same_result_as_add_trail_calls(trails):
    other = TrailMap()
    for name in ["Alpe", "Berg", "Col", "Dent", "Eck"]:
        other.add_hut(name)
    other.add_trail("Alpe", "Berg")
    other.add_trail("Col", "Dent")
    for a, b in [("Eck", "Col"), ("Col", "Berg"), ("Berg", "Dent")]:
        other.add_trail(a, b)
    trails.add_route(["Eck", "Col", "Berg", "Dent"])
    assert state(trails) == state(other)


def test_route_trails_are_ordinary_trails(trails):
    trails.add_route(["Eck", "Col", "Alpe"])
    trails.remove_trail("Col", "Eck")
    assert trails.get_neighbors("Col") == ["Dent", "Alpe"]
    assert trails.close_hut("Alpe") == 2
    with pytest.raises(TrailError):
        trails.add_trail("Dent", "Col")


def test_a_route_keeps_the_list_of_huts(trails):
    trails.add_route(["Dent", "Eck"])
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck"]


# --- failed routes add nothing ----------------------------------------------------


def test_a_route_through_an_existing_trail_adds_nothing(trails):
    before = state(trails)
    with pytest.raises(TrailError):
        trails.add_route(["Eck", "Dent", "Col", "Alpe"])
    assert state(trails) == before


def test_an_existing_trail_in_either_direction_fails_the_route(trails):
    before = state(trails)
    with pytest.raises(TrailError):
        trails.add_route(["Eck", "Berg", "Alpe"])
    assert state(trails) == before


def test_a_route_that_repeats_its_own_trail_adds_nothing(trails):
    before = state(trails)
    with pytest.raises(TrailError):
        trails.add_route(["Eck", "Col", "Eck"])
    with pytest.raises(TrailError):
        trails.add_route(["Alpe", "Eck", "Dent", "Eck"])
    assert state(trails) == before


@pytest.mark.parametrize(
    "huts",
    [
        ["Fluh", "Eck", "Alpe"],
        ["Eck", "Fluh", "Alpe"],
        ["Eck", "Alpe", "Fluh"],
    ],
    ids=["first", "middle", "last"],
)
def test_a_hut_not_in_use_fails_the_whole_route(trails, huts):
    before = state(trails)
    with pytest.raises(KeyError):
        trails.add_route(huts)
    assert state(trails) == before


def test_a_closed_hut_fails_the_whole_route(trails):
    trails.close_hut("Col")
    before = state(trails)
    with pytest.raises(KeyError):
        trails.add_route(["Eck", "Dent", "Col"])
    assert state(trails) == before


def test_the_same_hut_twice_in_a_row_fails_the_whole_route(trails):
    before = state(trails)
    with pytest.raises(ValueError):
        trails.add_route(["Eck", "Dent", "Dent", "Alpe"])
    assert state(trails) == before


def test_a_failed_route_can_be_followed_by_a_good_one(trails):
    with pytest.raises(TrailError):
        trails.add_route(["Eck", "Alpe", "Berg"])
    trails.add_route(["Eck", "Alpe", "Dent"])
    assert trails.get_neighbors("Alpe") == ["Berg", "Eck", "Dent"]
    assert trails.get_neighbors("Eck") == ["Alpe"]
