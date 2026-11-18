"""Hidden tests for the initial grain_silos spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest private/test_silos_initial.py
"""

import pytest
from silos import NotEnoughGrain, SiloError, Silos


@pytest.fixture
def silos():
    s = Silos()
    for name in ["north", "south", "east"]:
        s.add_silo(name)
    s.load("north", "wheat", 40)
    s.load("north", "barley", 15)
    return s


def state(s):
    """Every silo in order with its grains and tonnes, to check that a
    failed call changed nothing."""
    return [(n, [(g, s.get_tonnes(n, g)) for g in s.get_grains(n)]) for n in s.get_silos()]


# --- silos --------------------------------------------------------------------


def test_a_new_silo_is_empty():
    s = Silos()
    s.add_silo("north")
    assert s.get_grains("north") == []
    assert s.get_tonnes("north", "wheat") == 0


def test_a_new_object_has_no_silos():
    assert Silos().get_silos() == []


def test_silos_are_listed_in_the_order_added():
    s = Silos()
    for name in ["south", "north", "east"]:
        s.add_silo(name)
    assert s.get_silos() == ["south", "north", "east"]


def test_adding_a_name_in_use_is_rejected(silos):
    before = state(silos)
    with pytest.raises(SiloError):
        silos.add_silo("north")
    assert state(silos) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.load("west", "wheat", 1),
        lambda s: s.blend_into("west", "south"),
        lambda s: s.blend_into("north", "west"),
        lambda s: s.demolish_silo("west", "south"),
        lambda s: s.demolish_silo("north", "west"),
        lambda s: s.get_tonnes("west", "wheat"),
        lambda s: s.get_grains("west"),
    ],
)
def test_silos_that_were_never_added_raise_key_error(silos, call):
    before = state(silos)
    with pytest.raises(KeyError):
        call(silos)
    assert state(silos) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.load("east", "wheat", 1),
        lambda s: s.blend_into("east", "south"),
        lambda s: s.blend_into("north", "east"),
        lambda s: s.demolish_silo("east", "south"),
        lambda s: s.demolish_silo("north", "east"),
        lambda s: s.get_tonnes("east", "wheat"),
        lambda s: s.get_grains("east"),
    ],
)
def test_a_demolished_silo_is_not_in_use(silos, call):
    silos.demolish_silo("east", "south")  # east is empty
    before = state(silos)
    with pytest.raises(KeyError):
        call(silos)
    assert state(silos) == before


# --- loading and unloading ------------------------------------------------------


def test_loads_and_unloads_add_up(silos):
    silos.load("north", "wheat", 10)
    silos.unload("north", "wheat", 45)
    silos.load("south", "wheat", 2)
    assert silos.get_tonnes("north", "wheat") == 5
    assert silos.get_tonnes("south", "wheat") == 2
    assert silos.get_tonnes("north", "barley") == 15


def test_a_grain_never_held_has_0_tonnes(silos):
    assert silos.get_tonnes("north", "rye") == 0
    assert silos.get_tonnes("east", "wheat") == 0


def test_grains_are_listed_alphabetically(silos):
    for grain in ["rye", "corn", "oats"]:
        silos.load("south", grain, 3)
    assert silos.get_grains("south") == ["corn", "oats", "rye"]
    assert silos.get_grains("north") == ["barley", "wheat"]


def test_all_of_a_grain_can_be_unloaded(silos):
    silos.unload("north", "barley", 15)
    assert silos.get_tonnes("north", "barley") == 0
    assert silos.get_grains("north") == ["wheat"]


def test_unloading_more_than_the_silo_holds_changes_nothing(silos):
    before = state(silos)
    with pytest.raises(NotEnoughGrain):
        silos.unload("north", "barley", 16)
    with pytest.raises(NotEnoughGrain):
        silos.unload("north", "rye", 1)
    with pytest.raises(NotEnoughGrain):
        silos.unload("south", "wheat", 1)
    assert state(silos) == before


@pytest.mark.parametrize("tonnes", [0, -4])
@pytest.mark.parametrize(
    "call",
    [lambda s, t: s.load("north", "wheat", t), lambda s, t: s.unload("north", "wheat", t)],
    ids=["load", "unload"],
)
def test_tonnes_of_0_or_less_are_rejected(silos, call, tonnes):
    before = state(silos)
    with pytest.raises(ValueError):
        call(silos, tonnes)
    assert state(silos) == before


# --- blending -------------------------------------------------------------------


def test_blend_into_moves_every_grain(silos):
    silos.load("south", "wheat", 1)
    silos.load("south", "corn", 6)
    assert silos.blend_into("north", "south") == 55
    assert silos.get_grains("north") == []
    assert silos.get_grains("south") == ["barley", "corn", "wheat"]
    assert silos.get_tonnes("south", "wheat") == 41
    assert silos.get_tonnes("south", "barley") == 15
    assert silos.get_silos() == ["north", "south", "east"]


def test_blending_an_empty_silo_moves_nothing(silos):
    before = state(silos)
    assert silos.blend_into("east", "north") == 0
    assert state(silos) == before


def test_a_blended_silo_stays_in_use(silos):
    silos.blend_into("north", "east")
    silos.load("north", "oats", 2)
    assert silos.get_grains("north") == ["oats"]
    assert silos.get_grains("east") == ["barley", "wheat"]
    assert silos.blend_into("east", "north") == 55
    assert silos.get_tonnes("north", "wheat") == 40


# --- demolishing ----------------------------------------------------------------


def test_demolish_moves_all_the_grain_and_removes_the_silo(silos):
    silos.load("east", "wheat", 5)
    assert silos.demolish_silo("north", "east") == 55
    assert silos.get_silos() == ["south", "east"]
    assert silos.get_tonnes("east", "wheat") == 45
    assert silos.get_tonnes("east", "barley") == 15


def test_demolishing_an_empty_silo_moves_nothing(silos):
    assert silos.demolish_silo("south", "north") == 0
    assert silos.get_silos() == ["north", "east"]
    assert silos.get_tonnes("north", "wheat") == 40


def test_the_other_silos_keep_their_order_after_a_demolish(silos):
    silos.add_silo("west")
    silos.demolish_silo("south", "west")
    assert silos.get_silos() == ["north", "east", "west"]
    silos.demolish_silo("north", "east")
    assert silos.get_silos() == ["east", "west"]


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.blend_into("north", "north"),
        lambda s: s.demolish_silo("north", "north"),
        lambda s: s.blend_into("east", "east"),
    ],
    ids=["blend_into", "demolish_silo", "blend_into_empty"],
)
def test_the_same_silo_on_both_sides_is_rejected(silos, call):
    before = state(silos)
    with pytest.raises(ValueError):
        call(silos)
    assert state(silos) == before


# --- general --------------------------------------------------------------------


def test_not_enough_grain_is_a_silo_error():
    assert issubclass(NotEnoughGrain, SiloError)


def test_objects_do_not_share_silos():
    first, second = Silos(), Silos()
    first.add_silo("north")
    first.load("north", "wheat", 3)
    assert second.get_silos() == []
    second.add_silo("north")
    assert second.get_tonnes("north", "wheat") == 0
