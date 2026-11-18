"""Public checks for silos.py.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest public/test_silos_public.py
"""

import pytest
from silos import NotEnoughGrain, Silos


@pytest.fixture
def silos():
    s = Silos()
    s.add_silo("north")
    s.add_silo("south")
    return s


def test_loading_and_unloading_change_the_tonnes(silos):
    silos.load("north", "wheat", 40)
    silos.load("north", "wheat", 10)
    silos.unload("north", "wheat", 15)
    assert silos.get_tonnes("north", "wheat") == 35


def test_unloading_more_than_the_silo_holds_raises(silos):
    silos.load("north", "oats", 8)
    with pytest.raises(NotEnoughGrain):
        silos.unload("north", "oats", 9)
    assert silos.get_tonnes("north", "oats") == 8


def test_a_grain_whose_tonnes_all_left_is_not_listed(silos):
    silos.load("north", "wheat", 40)
    silos.load("north", "barley", 5)
    silos.unload("north", "barley", 5)
    assert silos.get_grains("north") == ["wheat"]


def test_blend_into_moves_every_grain_and_returns_the_tonnes(silos):
    silos.load("north", "wheat", 40)
    silos.load("north", "barley", 15)
    silos.load("south", "wheat", 5)
    assert silos.blend_into("north", "south") == 55
    assert silos.get_grains("north") == []
    assert silos.get_grains("south") == ["barley", "wheat"]
    assert silos.get_tonnes("south", "wheat") == 45
    assert silos.get_silos() == ["north", "south"]


def test_a_demolished_silo_is_gone(silos):
    silos.load("north", "rye", 12)
    silos.load("south", "rye", 3)
    assert silos.demolish_silo("north", "south") == 12
    assert silos.get_silos() == ["south"]
    assert silos.get_tonnes("south", "rye") == 15
    with pytest.raises(KeyError):
        silos.get_grains("north")
    with pytest.raises(KeyError):
        silos.load("north", "rye", 1)


def test_demolishing_an_empty_silo_returns_0(silos):
    silos.load("north", "wheat", 7)
    assert silos.demolish_silo("south", "north") == 0
    assert silos.get_silos() == ["north"]
    assert silos.get_tonnes("north", "wheat") == 7
