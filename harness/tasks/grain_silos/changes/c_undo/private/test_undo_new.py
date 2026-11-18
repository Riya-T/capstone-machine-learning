"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from silos import NotEnoughGrain, SiloError, Silos


@pytest.fixture
def silos():
    s = Silos()
    for name in ["north", "south", "east"]:
        s.add_silo(name)
    s.load("north", "wheat", 30)
    s.load("north", "barley", 20)
    s.load("south", "rye", 40)
    return s


def state(s):
    return [(n, [(g, s.get_tonnes(n, g)) for g in s.get_grains(n)]) for n in s.get_silos()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_a_load_of_a_new_grain(silos):
    before = state(silos)
    silos.load("east", "corn", 12)
    silos.undo()
    assert state(silos) == before
    assert silos.get_grains("east") == []


def test_undo_of_a_load_of_more_grain(silos):
    silos.load("north", "wheat", 5)
    silos.undo()
    assert silos.get_tonnes("north", "wheat") == 30


def test_undo_of_an_unload(silos):
    before = state(silos)
    silos.unload("north", "wheat", 10)
    silos.undo()
    assert state(silos) == before


def test_undo_of_unloading_all_of_a_grain(silos):
    before = state(silos)
    silos.unload("north", "barley", 20)
    silos.undo()
    assert state(silos) == before
    assert silos.get_grains("north") == ["barley", "wheat"]


def test_undo_of_blend_into_restores_both_silos(silos):
    before = state(silos)
    assert silos.blend_into("north", "south") == 50
    silos.undo()
    assert state(silos) == before
    assert silos.get_grains("south") == ["rye"]


def test_undo_of_blend_into_an_empty_silo(silos):
    before = state(silos)
    silos.blend_into("south", "east")
    silos.undo()
    assert state(silos) == before
    assert silos.get_grains("east") == []


def test_undo_of_demolish_brings_the_silo_back_with_its_grain(silos):
    before = state(silos)
    assert silos.demolish_silo("north", "east") == 50
    silos.undo()
    assert state(silos) == before
    assert silos.get_silos() == ["north", "south", "east"]
    assert silos.get_tonnes("east", "wheat") == 0


def test_undo_of_demolish_keeps_its_place_in_the_list(silos):
    silos.add_silo("west")
    before = state(silos)
    silos.demolish_silo("south", "west")
    assert silos.get_silos() == ["north", "east", "west"]
    silos.undo()
    assert silos.get_silos() == ["north", "south", "east", "west"]
    assert state(silos) == before


def test_a_silo_brought_back_is_in_use_again(silos):
    silos.demolish_silo("north", "east")
    silos.undo()
    silos.load("north", "wheat", 1)
    assert silos.get_tonnes("north", "wheat") == 31
    with pytest.raises(SiloError):
        silos.add_silo("north")
    assert silos.demolish_silo("north", "south") == 51
    assert silos.get_silos() == ["south", "east"]


def test_undo_of_add_silo_removes_it_and_frees_the_name(silos):
    silos.add_silo("west")
    silos.undo()
    assert silos.get_silos() == ["north", "south", "east"]
    with pytest.raises(KeyError):
        silos.get_grains("west")
    silos.add_silo("west")
    assert silos.get_silos() == ["north", "south", "east", "west"]
    assert silos.get_grains("west") == []


def test_undo_of_two_demolishes_in_a_row(silos):
    before = state(silos)
    silos.demolish_silo("north", "east")
    silos.demolish_silo("east", "south")
    assert silos.get_silos() == ["south"]
    assert silos.get_grains("south") == ["barley", "rye", "wheat"]
    silos.undo()
    assert state(silos) == [("south", [("rye", 40)]), ("east", [("barley", 20), ("wheat", 30)])]
    silos.undo()
    assert state(silos) == before


# --- calls that move nothing ------------------------------------------------


def test_a_blend_of_nothing_is_still_a_call(silos):
    silos.load("east", "oats", 3)
    silos.unload("east", "oats", 3)
    assert silos.blend_into("east", "north") == 0
    silos.undo()  # the blend, which changed nothing
    assert silos.get_grains("east") == []
    silos.undo()  # the unload
    assert silos.get_tonnes("east", "oats") == 3


def test_demolishing_an_empty_silo_can_be_undone(silos):
    silos.load("south", "rye", 1)
    assert silos.demolish_silo("east", "south") == 0
    silos.undo()
    assert silos.get_silos() == ["north", "south", "east"]
    assert silos.get_tonnes("south", "rye") == 41
    silos.undo()
    assert silos.get_tonnes("south", "rye") == 40


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    s = Silos()
    calls = [
        lambda: s.add_silo("north"),
        lambda: s.add_silo("south"),
        lambda: s.load("north", "wheat", 30),
        lambda: s.load("north", "barley", 20),
        lambda: s.add_silo("east"),
        lambda: s.load("south", "rye", 40),
        lambda: s.unload("north", "wheat", 5),
        lambda: s.blend_into("north", "east"),
        lambda: s.demolish_silo("south", "east"),
        lambda: s.add_silo("west"),
        lambda: s.load("west", "corn", 7),
        lambda: s.blend_into("east", "west"),
        lambda: s.demolish_silo("west", "north"),
    ]
    states = [state(s)]
    for call in calls:
        call()
        states.append(state(s))
    assert s.get_silos() == ["north", "east"]
    assert s.get_tonnes("north", "rye") == 40
    assert s.get_tonnes("north", "corn") == 7
    for expected in reversed(states[:-1]):
        s.undo()
        assert state(s) == expected
    with pytest.raises(SiloError):
        s.undo()
    assert s.get_silos() == []


def test_failed_calls_are_not_recorded(silos):
    silos.load("east", "corn", 12)
    for call in (
        lambda: silos.unload("north", "wheat", 99),
        lambda: silos.unload("north", "oats", 1),
        lambda: silos.blend_into("north", "north"),
        lambda: silos.blend_into("north", "west"),
        lambda: silos.demolish_silo("north", "north"),
        lambda: silos.demolish_silo("west", "north"),
        lambda: silos.add_silo("north"),
        lambda: silos.load("west", "wheat", 1),
        lambda: silos.load("north", "wheat", 0),
    ):
        with pytest.raises((ValueError, KeyError, SiloError)):
            call()
    silos.undo()  # the load of corn
    assert silos.get_grains("east") == []
    assert silos.get_tonnes("north", "wheat") == 30


def test_get_calls_are_not_recorded(silos):
    silos.load("east", "corn", 12)
    silos.get_tonnes("east", "corn")
    silos.get_grains("east")
    silos.get_silos()
    silos.undo()
    assert silos.get_grains("east") == []
    assert silos.get_tonnes("south", "rye") == 40


def test_there_is_no_redo():
    s = Silos()
    s.add_silo("north")
    s.load("north", "wheat", 3)
    s.undo()
    s.undo()
    assert s.get_silos() == []
    with pytest.raises(SiloError):
        s.undo()


def test_new_calls_after_an_undo_are_undone_first(silos):
    silos.load("east", "corn", 12)
    silos.undo()
    silos.load("east", "oats", 1)
    silos.undo()
    assert silos.get_grains("east") == []
    silos.undo()  # the load of rye in the fixture
    assert silos.get_grains("south") == []
    assert silos.get_grains("north") == ["barley", "wheat"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    s = Silos()
    with pytest.raises(SiloError):
        s.undo()
    s.add_silo("north")
    s.undo()
    with pytest.raises(SiloError):
        s.undo()
    assert s.get_silos() == []
    s.add_silo("north")
    s.load("north", "wheat", 1)
    assert s.get_tonnes("north", "wheat") == 1


def test_the_whole_fixture_can_be_undone(silos):
    for _ in range(6):
        silos.undo()
    assert silos.get_silos() == []
    with pytest.raises(SiloError):
        silos.undo()


def test_undo_restores_tonnes_that_a_later_call_checks(silos):
    silos.unload("north", "wheat", 30)
    silos.undo()
    assert silos.blend_into("north", "east") == 50
    assert silos.get_tonnes("east", "wheat") == 30
    with pytest.raises(NotEnoughGrain):
        silos.unload("north", "wheat", 1)
