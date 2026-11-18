"""Hidden tests for the undo change. Never shown to the writer or the
editor.

Usage (with trails.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_trail_undo_new.py
"""

import pytest
from trails import TrailError, TrailMap


@pytest.fixture
def trails():
    # Alpe-Berg, Col-Alpe, Berg-Col, Col-Dent; Eck has no trails.
    t = TrailMap()
    for name in ["Alpe", "Berg", "Col", "Dent", "Eck"]:
        t.add_hut(name)
    t.add_trail("Alpe", "Berg")
    t.add_trail("Col", "Alpe")
    t.add_trail("Berg", "Col")
    t.add_trail("Col", "Dent")
    return t


def state(t):
    return [(h, t.get_neighbors(h)) for h in t.get_huts()]


# --- simple calls -------------------------------------------------------------


def test_undo_of_add_trail_removes_it_from_both_huts(trails):
    before = state(trails)
    trails.add_trail("Eck", "Alpe")
    trails.undo()
    assert state(trails) == before
    trails.add_trail("Alpe", "Eck")
    assert trails.get_neighbors("Eck") == ["Alpe"]


def test_undo_of_remove_trail_puts_it_back_in_its_place(trails):
    before = state(trails)
    trails.remove_trail("Alpe", "Col")
    trails.undo()
    assert trails.get_neighbors("Alpe") == ["Berg", "Col"]
    assert trails.get_neighbors("Col") == ["Alpe", "Berg", "Dent"]
    assert state(trails) == before


def test_a_trail_put_back_by_undo_exists_again(trails):
    trails.remove_trail("Berg", "Alpe")
    trails.undo()
    with pytest.raises(TrailError):
        trails.add_trail("Alpe", "Berg")
    trails.remove_trail("Alpe", "Berg")
    assert trails.get_neighbors("Alpe") == ["Col"]


# --- composite calls are undone as a whole ------------------------------------


def test_one_undo_takes_back_a_whole_close_hut(trails):
    before = state(trails)
    assert trails.close_hut("Col") == 3
    trails.undo()
    assert state(trails) == before
    assert trails.get_neighbors("Col") == ["Alpe", "Berg", "Dent"]


def test_a_hut_brought_back_keeps_its_place_and_its_trails_places(trails):
    trails.add_trail("Berg", "Eck")
    before = state(trails)
    trails.close_hut("Berg")
    assert trails.get_huts() == ["Alpe", "Col", "Dent", "Eck"]
    trails.undo()
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck"]
    assert trails.get_neighbors("Alpe") == ["Berg", "Col"]
    assert trails.get_neighbors("Col") == ["Alpe", "Berg", "Dent"]
    assert state(trails) == before


def test_a_hut_brought_back_is_in_use_again(trails):
    trails.close_hut("Dent")
    trails.undo()
    with pytest.raises(TrailError):
        trails.add_hut("Dent")
    trails.add_trail("Dent", "Eck")
    assert trails.get_neighbors("Dent") == ["Col", "Eck"]
    assert trails.close_hut("Dent") == 2


def test_undo_of_closing_a_hut_with_no_trails_brings_it_back(trails):
    trails.close_hut("Eck")
    trails.undo()
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck"]
    assert trails.get_neighbors("Eck") == []


def test_one_undo_takes_back_a_whole_merge(trails):
    before = state(trails)
    trails.merge_huts("Col", "Eck")
    assert sorted(trails.get_neighbors("Eck")) == ["Alpe", "Berg", "Dent"]
    trails.undo()
    assert state(trails) == before
    assert trails.get_neighbors("Eck") == []


def test_undo_of_a_merge_puts_the_hut_back_in_its_neighbors_places(trails):
    before = state(trails)
    trails.merge_huts("Alpe", "Eck")
    assert trails.get_neighbors("Col") == ["Berg", "Dent", "Eck"]
    trails.undo()
    assert trails.get_neighbors("Col") == ["Alpe", "Berg", "Dent"]
    assert trails.get_neighbors("Berg") == ["Alpe", "Col"]
    assert state(trails) == before


def test_undo_of_a_merge_into_a_hut_with_trails(trails):
    trails.add_trail("Dent", "Eck")
    before = state(trails)
    trails.merge_huts("Alpe", "Eck")
    assert sorted(trails.get_neighbors("Eck")) == ["Berg", "Col", "Dent"]
    trails.undo()
    assert state(trails) == before
    assert trails.get_neighbors("Eck") == ["Dent"]
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck"]


def test_undo_of_add_hut_removes_it_and_frees_the_name(trails):
    trails.add_hut("Fluh")
    trails.undo()
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck"]
    with pytest.raises(KeyError):
        trails.get_neighbors("Fluh")
    trails.add_hut("Fluh")
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck", "Fluh"]


def test_undo_through_a_name_that_was_closed_and_added_again(trails):
    trails.add_hut("Fluh")
    trails.add_trail("Fluh", "Alpe")
    trails.close_hut("Fluh")
    trails.add_hut("Fluh")  # a new Fluh with no trails
    trails.add_trail("Fluh", "Eck")
    trails.undo()  # Fluh-Eck
    trails.undo()  # the new Fluh
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck"]
    trails.undo()  # the close: the old Fluh comes back with its trail
    assert trails.get_neighbors("Fluh") == ["Alpe"]
    assert trails.get_neighbors("Alpe") == ["Berg", "Col", "Fluh"]
    trails.undo()  # Fluh-Alpe
    trails.undo()  # the first Fluh
    assert trails.get_huts() == ["Alpe", "Berg", "Col", "Dent", "Eck"]
    assert trails.get_neighbors("Alpe") == ["Berg", "Col"]


# --- what is and is not recorded ----------------------------------------------


def test_each_undo_goes_one_call_further_back():
    t = TrailMap()
    calls = [
        lambda: t.add_hut("Alpe"),
        lambda: t.add_hut("Berg"),
        lambda: t.add_hut("Col"),
        lambda: t.add_trail("Alpe", "Berg"),
        lambda: t.add_trail("Col", "Alpe"),
        lambda: t.add_hut("Dent"),
        lambda: t.add_trail("Dent", "Berg"),
        lambda: t.remove_trail("Alpe", "Berg"),
        lambda: t.add_hut("Eck"),
        lambda: t.add_trail("Eck", "Dent"),
        lambda: t.merge_huts("Col", "Eck"),
        lambda: t.add_trail("Berg", "Eck"),
        lambda: t.close_hut("Dent"),
        lambda: t.add_hut("Fluh"),
        lambda: t.add_trail("Fluh", "Alpe"),
        lambda: t.merge_huts("Fluh", "Berg"),
    ]
    states = [state(t)]
    for call in calls:
        call()
        states.append(state(t))
    assert t.get_huts() == ["Alpe", "Berg", "Eck"]
    assert [sorted(t.get_neighbors(h)) for h in t.get_huts()] == [
        ["Berg", "Eck"], ["Alpe", "Eck"], ["Alpe", "Berg"]]
    for expected in reversed(states[:-1]):
        t.undo()
        assert state(t) == expected
    with pytest.raises(TrailError):
        t.undo()
    assert t.get_huts() == []


def test_failed_calls_are_not_recorded(trails):
    trails.add_trail("Eck", "Dent")
    for call in (
        lambda: trails.add_hut("Alpe"),
        lambda: trails.add_trail("Alpe", "Alpe"),
        lambda: trails.add_trail("Berg", "Alpe"),
        lambda: trails.add_trail("Alpe", "Fluh"),
        lambda: trails.remove_trail("Alpe", "Dent"),
        lambda: trails.close_hut("Fluh"),
        lambda: trails.merge_huts("Col", "Col"),
        lambda: trails.merge_huts("Fluh", "Col"),
    ):
        with pytest.raises((ValueError, KeyError, TrailError)):
            call()
    trails.undo()  # Eck-Dent
    assert trails.get_neighbors("Eck") == []
    trails.undo()  # Col-Dent from the fixture
    assert trails.get_neighbors("Col") == ["Alpe", "Berg"]


def test_get_calls_are_not_recorded(trails):
    trails.add_trail("Eck", "Dent")
    trails.get_neighbors("Eck")
    trails.get_huts()
    trails.undo()
    assert trails.get_neighbors("Eck") == []
    assert trails.get_neighbors("Dent") == ["Col"]


def test_there_is_no_redo():
    t = TrailMap()
    t.add_hut("Alpe")
    t.add_hut("Berg")
    t.add_trail("Alpe", "Berg")
    t.undo()
    t.undo()
    t.undo()
    assert t.get_huts() == []
    with pytest.raises(TrailError):
        t.undo()


def test_a_new_call_after_an_undo_is_undone_first(trails):
    trails.add_trail("Eck", "Alpe")
    trails.undo()
    trails.add_trail("Eck", "Berg")
    trails.undo()
    assert trails.get_neighbors("Eck") == []
    trails.undo()  # Col-Dent from the fixture
    assert trails.get_neighbors("Dent") == []
    assert trails.get_neighbors("Col") == ["Alpe", "Berg"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    t = TrailMap()
    with pytest.raises(TrailError):
        t.undo()
    t.add_hut("Alpe")
    t.undo()
    with pytest.raises(TrailError):
        t.undo()
    assert t.get_huts() == []
    t.add_hut("Alpe")
    assert t.get_huts() == ["Alpe"]


def test_the_whole_fixture_can_be_undone(trails):
    for _ in range(9):
        trails.undo()
    assert trails.get_huts() == []
    with pytest.raises(TrailError):
        trails.undo()
