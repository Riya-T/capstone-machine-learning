"""Hidden tests for the c_totals change (derived_value). Never shown to the
writer or the editor.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest changes/c_totals/private/test_totals_new.py
"""

import pytest
from silos import Silos


@pytest.fixture
def silos():
    s = Silos()
    for name in ["north", "south", "east"]:
        s.add_silo(name)
    s.load("north", "wheat", 30)
    s.load("north", "barley", 20)
    s.load("south", "rye", 40)
    s.load("south", "wheat", 7)
    return s


def state(s):
    return [(n, [(g, s.get_tonnes(n, g)) for g in s.get_grains(n)]) for n in s.get_silos()]


# --- get_total ----------------------------------------------------------------


def test_total_of_each_silo(silos):
    assert silos.get_total("north") == 50
    assert silos.get_total("south") == 47
    assert silos.get_total("east") == 0


def test_total_follows_loads_and_unloads(silos):
    silos.load("east", "corn", 4)
    silos.load("east", "corn", 6)
    silos.unload("north", "wheat", 30)
    assert silos.get_total("east") == 10
    assert silos.get_total("north") == 20


def test_total_after_blend_and_demolish(silos):
    silos.blend_into("north", "east")
    assert silos.get_total("north") == 0
    assert silos.get_total("east") == 50
    silos.demolish_silo("south", "east")
    assert silos.get_total("east") == 97


@pytest.mark.parametrize("name", ["west", "south"])
def test_total_of_a_silo_not_in_use_raises_key_error(silos, name):
    silos.demolish_silo("south", "north")
    with pytest.raises(KeyError):
        silos.get_total(name)


def test_a_new_silo_has_a_total_of_0():
    s = Silos()
    s.add_silo("north")
    assert s.get_total("north") == 0


# --- get_grain_total ----------------------------------------------------------


def test_grain_total_over_every_silo(silos):
    assert silos.get_grain_total("wheat") == 37
    assert silos.get_grain_total("barley") == 20
    assert silos.get_grain_total("rye") == 40


def test_a_grain_nobody_holds_has_a_total_of_0(silos):
    assert silos.get_grain_total("corn") == 0
    assert Silos().get_grain_total("wheat") == 0


def test_grain_total_follows_loads_and_unloads(silos):
    silos.load("east", "wheat", 3)
    silos.unload("south", "wheat", 7)
    assert silos.get_grain_total("wheat") == 33
    silos.unload("north", "barley", 20)
    assert silos.get_grain_total("barley") == 0


def test_moving_grain_keeps_its_total(silos):
    silos.blend_into("north", "south")
    assert silos.get_grain_total("wheat") == 37
    silos.demolish_silo("south", "east")
    assert silos.get_grain_total("wheat") == 37
    assert silos.get_grain_total("rye") == 40
    assert silos.get_total("east") == 97


def test_a_demolished_silo_no_longer_counts_separately(silos):
    silos.demolish_silo("north", "east")
    assert silos.get_silos() == ["south", "east"]
    assert silos.get_grain_total("barley") == 20
    assert silos.get_total("east") == 50


# --- nothing changes ----------------------------------------------------------


def test_the_totals_change_nothing(silos):
    before = state(silos)
    silos.get_total("north")
    silos.get_grain_total("wheat")
    assert state(silos) == before
