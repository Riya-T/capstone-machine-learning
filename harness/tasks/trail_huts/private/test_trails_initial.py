"""Hidden tests for the initial trail_huts spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with trails.py importable, e.g. in the sandbox):
    python -m pytest private/test_trails_initial.py
"""

import pytest
from trails import TrailError, TrailMap


@pytest.fixture
def trails():
    # Alpe-Berg, Alpe-Col, Berg-Col, Col-Dent; Eck has no trails.
    t = TrailMap()
    for name in ["Alpe", "Berg", "Col", "Dent", "Eck"]:
        t.add_hut(name)
    t.add_trail("Alpe", "Berg")
    t.add_trail("Col", "Alpe")
    t.add_trail("Berg", "Col")
    t.add_trail("Col", "Dent")
    return t


def state(t):
    """Every hut in order with its neighbors in order, to check that a failed
    call changed nothing."""
    return [(h, t.get_neighbors(h)) for h in t.get_huts()]


def others(t, *skip):
    """Like state, without the given huts (the order of a merge's into_hut is
    unspecified)."""
    return [(h, n) for h, n in state(t) if h not in skip]


# --- huts -------------------------------------------------------------------


def test_a_new_hut_has_no_trails():
    t = TrailMap()
    t.add_hut("Alpe")
    assert t.get_neighbors("Alpe") == []


def test_huts_keep_the_order_they_were_added_in():
    t = TrailMap()
    for name in ["Dent", "Alpe", "Col", "Berg"]:
        t.add_hut(name)
    assert t.get_huts() == ["Dent", "Alpe", "Col", "Berg"]


def test_a_hut_name_in_use_cannot_be_added_again(trails):
    before = state(trails)
    with pytest.raises(TrailError):
        trails.add_hut("Col")
    assert state(trails) == before


def test_a_closed_name_can_be_added_again_as_a_new_hut(trails):
    trails.close_hut("Alpe")
    trails.add_hut("Alpe")
    assert trails.get_huts() == ["Berg", "Col", "Dent", "Eck", "Alpe"]
    assert trails.get_neighbors("Alpe") == []
    assert trails.get_neighbors("Berg") == ["Col"]


def test_a_merged_name_can_be_added_again_as_a_new_hut(trails):
    trails.merge_huts("Dent", "Eck")
    trails.add_hut("Dent")
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Eck", "Dent"]
    assert trails.get_neighbors("Dent") == []


@pytest.mark.parametrize(
    "call",
    [
        lambda t: t.add_trail("Alpe", "Fluh"),
        lambda t: t.add_trail("Fluh", "Alpe"),
        lambda t: t.remove_trail("Alpe", "Fluh"),
        lambda t: t.close_hut("Fluh"),
        lambda t: t.merge_huts("Fluh", "Alpe"),
        lambda t: t.merge_huts("Alpe", "Fluh"),
        lambda t: t.get_neighbors("Fluh"),
    ],
)
def test_huts_never_added_raise_key_error(trails, call):
    before = state(trails)
    with pytest.raises(KeyError):
        call(trails)
    assert state(trails) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda t: t.add_trail("Eck", "Dent"),
        lambda t: t.remove_trail("Eck", "Dent"),
        lambda t: t.close_hut("Dent"),
        lambda t: t.merge_huts("Dent", "Eck"),
        lambda t: t.merge_huts("Eck", "Dent"),
        lambda t: t.get_neighbors("Dent"),
    ],
)
def test_a_closed_hut_is_not_in_use(trails, call):
    trails.close_hut("Dent")
    before = state(trails)
    with pytest.raises(KeyError):
        call(trails)
    assert state(trails) == before


# --- adding and removing trails -------------------------------------------------


def test_a_trail_is_listed_at_both_huts_in_the_order_added(trails):
    assert trails.get_neighbors("Alpe") == ["Berg", "Col"]
    assert trails.get_neighbors("Berg") == ["Alpe", "Col"]
    assert trails.get_neighbors("Col") == ["Alpe", "Berg", "Dent"]
    assert trails.get_neighbors("Dent") == ["Col"]
    assert trails.get_neighbors("Eck") == []


def test_a_new_trail_comes_last(trails):
    trails.add_trail("Eck", "Col")
    assert trails.get_neighbors("Col") == ["Alpe", "Berg", "Dent", "Eck"]
    assert trails.get_neighbors("Eck") == ["Col"]


def test_a_trail_to_the_same_hut_is_rejected(trails):
    before = state(trails)
    with pytest.raises(ValueError):
        trails.add_trail("Alpe", "Alpe")
    assert state(trails) == before


def test_a_trail_that_exists_is_rejected_in_either_order(trails):
    before = state(trails)
    with pytest.raises(TrailError):
        trails.add_trail("Alpe", "Berg")
    with pytest.raises(TrailError):
        trails.add_trail("Berg", "Alpe")
    assert state(trails) == before


def test_remove_trail_works_in_either_order(trails):
    trails.remove_trail("Berg", "Alpe")
    trails.remove_trail("Col", "Dent")
    assert trails.get_neighbors("Alpe") == ["Col"]
    assert trails.get_neighbors("Berg") == ["Col"]
    assert trails.get_neighbors("Col") == ["Alpe", "Berg"]
    assert trails.get_neighbors("Dent") == []


def test_removing_a_trail_that_does_not_exist_raises(trails):
    before = state(trails)
    with pytest.raises(TrailError):
        trails.remove_trail("Alpe", "Dent")
    with pytest.raises(TrailError):
        trails.remove_trail("Eck", "Col")
    assert state(trails) == before


def test_a_trail_added_again_after_removal_comes_last(trails):
    trails.remove_trail("Col", "Alpe")
    trails.add_trail("Alpe", "Col")
    assert trails.get_neighbors("Col") == ["Berg", "Dent", "Alpe"]
    assert trails.get_neighbors("Alpe") == ["Berg", "Col"]


# --- closing ----------------------------------------------------------------


def test_close_hut_removes_every_trail_and_returns_how_many(trails):
    assert trails.close_hut("Col") == 3
    assert trails.get_huts() == ["Alpe", "Berg", "Dent", "Eck"]
    assert state(trails) == [("Alpe", ["Berg"]), ("Berg", ["Alpe"]), ("Dent", []), ("Eck", [])]


def test_closing_a_hut_with_no_trails_returns_0(trails):
    assert trails.close_hut("Eck") == 0
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent"]


def test_closing_keeps_the_other_trails_in_order(trails):
    trails.add_trail("Col", "Eck")
    trails.close_hut("Berg")
    assert trails.get_neighbors("Col") == ["Alpe", "Dent", "Eck"]
    assert trails.get_huts() == ["Alpe", "Col", "Dent", "Eck"]


# --- merging ----------------------------------------------------------------


def test_merge_into_a_hut_with_no_trails(trails):
    trails.merge_huts("Col", "Eck")
    assert trails.get_huts() == ["Alpe", "Berg", "Dent", "Eck"]
    assert sorted(trails.get_neighbors("Eck")) == ["Alpe", "Berg", "Dent"]
    assert others(trails, "Eck") == [
        ("Alpe", ["Berg", "Eck"]),
        ("Berg", ["Alpe", "Eck"]),
        ("Dent", ["Eck"]),
    ]


def test_merge_into_a_hut_that_has_trails(trails):
    trails.add_hut("Fluh")
    trails.add_trail("Eck", "Fluh")
    trails.merge_huts("Col", "Eck")  # Col's neighbors: Alpe, Berg, Dent
    assert sorted(trails.get_neighbors("Eck")) == ["Alpe", "Berg", "Dent", "Fluh"]
    assert others(trails, "Eck") == [
        ("Alpe", ["Berg", "Eck"]),
        ("Berg", ["Alpe", "Eck"]),
        ("Dent", ["Eck"]),
        ("Fluh", ["Eck"]),
    ]


def test_merge_keeps_the_other_trails_of_each_neighbor_in_order(trails):
    trails.add_trail("Eck", "Dent")
    trails.add_hut("Fluh")
    trails.merge_huts("Alpe", "Fluh")  # Alpe's neighbors: Berg, Col
    assert sorted(trails.get_neighbors("Fluh")) == ["Berg", "Col"]
    assert trails.get_neighbors("Col") == ["Berg", "Dent", "Fluh"]
    assert trails.get_neighbors("Berg") == ["Col", "Fluh"]
    assert trails.get_neighbors("Dent") == ["Col", "Eck"]
    assert trails.get_huts() == ["Berg", "Col", "Dent", "Eck", "Fluh"]


def test_merging_a_hut_with_no_trails_removes_it(trails):
    before = others(trails, "Eck", "Alpe")
    trails.merge_huts("Eck", "Alpe")
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent"]
    assert sorted(trails.get_neighbors("Alpe")) == ["Berg", "Col"]
    assert others(trails, "Alpe") == before


def test_merging_a_hut_into_itself_is_rejected(trails):
    before = state(trails)
    with pytest.raises(ValueError):
        trails.merge_huts("Col", "Col")
    assert state(trails) == before


# --- general ----------------------------------------------------------------


def test_maps_do_not_share_huts():
    first, second = TrailMap(), TrailMap()
    first.add_hut("Alpe")
    first.add_hut("Berg")
    first.add_trail("Alpe", "Berg")
    assert second.get_huts() == []
    second.add_hut("Alpe")
    assert second.get_neighbors("Alpe") == []
