"""Hidden tests for the trail limit change. Never shown to the writer or the
editor.

Usage (with trails.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limit/private/test_limit_new.py
"""

import pytest
from trails import TooManyTrails, TrailError, TrailMap


@pytest.fixture
def trails():
    # Alpe has 2 of at most 2 trails, Col 2 of at most 3, Eck 0 of at most 1;
    # Berg and Dent have no limit.
    t = TrailMap()
    t.add_hut("Alpe", max_trails=2)
    t.add_hut("Berg")
    t.add_hut("Col", max_trails=3)
    t.add_hut("Dent")
    t.add_hut("Eck", max_trails=1)
    t.add_trail("Alpe", "Berg")
    t.add_trail("Col", "Alpe")
    t.add_trail("Berg", "Col")
    return t


def state(t):
    return [(h, t.get_neighbors(h)) for h in t.get_huts()]


# --- the limit ------------------------------------------------------------------


def test_get_max_trails_returns_the_limit_or_none(trails):
    assert [trails.get_max_trails(h) for h in trails.get_huts()] == [2, None, 3, None, 1]


def test_a_hut_added_without_a_limit_has_none(trails):
    trails.add_hut("Fluh")
    assert trails.get_max_trails("Fluh") is None
    for hut in ["Berg", "Col", "Dent", "Eck"]:
        trails.add_trail("Fluh", hut)
    assert trails.get_neighbors("Fluh") == ["Berg", "Col", "Dent", "Eck"]


@pytest.mark.parametrize("limit", [0, -1])
def test_a_limit_of_0_or_less_adds_no_hut(trails, limit):
    before = state(trails)
    with pytest.raises(ValueError):
        trails.add_hut("Fluh", max_trails=limit)
    assert state(trails) == before
    trails.add_hut("Fluh", max_trails=2)
    assert trails.get_max_trails("Fluh") == 2


def test_get_max_trails_of_a_hut_not_in_use_raises_key_error(trails):
    with pytest.raises(KeyError):
        trails.get_max_trails("Fluh")
    trails.close_hut("Eck")
    with pytest.raises(KeyError):
        trails.get_max_trails("Eck")


def test_too_many_trails_is_a_trail_error():
    assert issubclass(TooManyTrails, TrailError)


# --- add_trail --------------------------------------------------------------------


def test_add_trail_up_to_exactly_the_limit(trails):
    trails.add_trail("Col", "Dent")
    assert trails.get_neighbors("Col") == ["Alpe", "Berg", "Dent"]
    trails.add_trail("Eck", "Dent")
    assert trails.get_neighbors("Eck") == ["Dent"]


def test_add_trail_to_a_full_hut_is_refused_from_either_side(trails):
    before = state(trails)
    with pytest.raises(TooManyTrails):
        trails.add_trail("Alpe", "Dent")
    with pytest.raises(TooManyTrails):
        trails.add_trail("Dent", "Alpe")
    assert state(trails) == before


def test_add_trail_is_refused_when_the_other_hut_is_full(trails):
    trails.add_trail("Eck", "Dent")
    before = state(trails)
    with pytest.raises(TooManyTrails):
        trails.add_trail("Berg", "Eck")
    assert state(trails) == before


def test_removing_a_trail_makes_room(trails):
    trails.remove_trail("Berg", "Alpe")
    trails.add_trail("Alpe", "Dent")
    assert trails.get_neighbors("Alpe") == ["Col", "Dent"]


def test_close_hut_never_checks_limits(trails):
    assert trails.close_hut("Alpe") == 2
    assert trails.close_hut("Col") == 1
    assert trails.get_huts() == ["Berg", "Dent", "Eck"]


# --- merge_huts -------------------------------------------------------------------


def test_merge_into_a_hut_with_room(trails):
    trails.add_hut("Fluh")
    trails.add_trail("Fluh", "Eck")
    trails.merge_huts("Fluh", "Col")  # Col ends with 3 trails, its limit
    assert sorted(trails.get_neighbors("Col")) == ["Alpe", "Berg", "Eck"]
    assert trails.get_neighbors("Eck") == ["Col"]


def test_merge_that_would_go_over_the_limit_changes_nothing(trails):
    trails.add_trail("Dent", "Berg")
    trails.add_hut("Fluh")
    trails.add_trail("Dent", "Fluh")
    before = state(trails)
    with pytest.raises(TooManyTrails):
        trails.merge_huts("Dent", "Eck")
    assert state(trails) == before
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck", "Fluh"]


def test_merge_does_not_check_the_limits_of_the_other_huts(trails):
    trails.add_trail("Eck", "Dent")  # Eck is now full
    trails.merge_huts("Dent", "Berg")  # Eck-Dent becomes Eck-Berg
    assert trails.get_neighbors("Eck") == ["Berg"]
    assert sorted(trails.get_neighbors("Berg")) == ["Alpe", "Col", "Eck"]


def test_a_name_added_again_gets_its_own_limit(trails):
    trails.close_hut("Alpe")
    trails.add_hut("Alpe")
    assert trails.get_max_trails("Alpe") is None
    trails.merge_huts("Eck", "Dent")
    trails.add_hut("Eck", max_trails=2)
    assert trails.get_max_trails("Eck") == 2
    trails.add_trail("Eck", "Alpe")
    trails.add_trail("Eck", "Berg")
    with pytest.raises(TooManyTrails):
        trails.add_trail("Eck", "Dent")


# --- undo -------------------------------------------------------------------------


def test_an_undone_close_brings_the_hut_back_with_its_limit(trails):
    trails.close_hut("Alpe")
    trails.undo()
    assert trails.get_max_trails("Alpe") == 2
    assert trails.get_neighbors("Alpe") == ["Berg", "Col"]
    with pytest.raises(TooManyTrails):
        trails.add_trail("Alpe", "Dent")


def test_an_undone_add_hut_frees_the_name_for_any_limit(trails):
    trails.add_hut("Fluh", max_trails=1)
    trails.undo()
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck"]
    trails.add_hut("Fluh", max_trails=2)
    assert trails.get_max_trails("Fluh") == 2
    trails.add_trail("Fluh", "Berg")
    trails.add_trail("Fluh", "Dent")
    assert trails.get_neighbors("Fluh") == ["Berg", "Dent"]


def test_undo_of_a_trail_makes_room_again(trails):
    trails.add_trail("Eck", "Dent")
    trails.undo()
    trails.add_trail("Eck", "Berg")
    assert trails.get_neighbors("Eck") == ["Berg"]


def test_a_refused_call_is_not_undone(trails):
    trails.add_trail("Col", "Dent")
    with pytest.raises(TooManyTrails):
        trails.add_trail("Col", "Eck")
    trails.undo()  # Col-Dent
    assert trails.get_neighbors("Col") == ["Alpe", "Berg"]
    assert trails.get_neighbors("Eck") == []
