"""Hidden tests for the c_seal change (state_flag). Never shown to the writer
or the editor.

Usage (with silos.py importable, e.g. in the sandbox):
    python -m pytest changes/c_seal/private/test_seal_new.py
"""

import pytest
from silos import SiloError, SiloSealed, Silos


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


# --- seal, unseal and get_sealed ----------------------------------------------


def test_new_silos_are_not_sealed(silos):
    assert silos.get_sealed() == []


def test_sealed_silos_are_listed_in_silo_order(silos):
    silos.seal("east")
    silos.seal("north")
    assert silos.get_sealed() == ["north", "east"]


def test_sealing_twice_and_unsealing_an_unsealed_silo_do_nothing(silos):
    silos.seal("north")
    silos.seal("north")
    assert silos.get_sealed() == ["north"]
    silos.unseal("south")
    assert silos.get_sealed() == ["north"]
    silos.unseal("north")
    assert silos.get_sealed() == []


@pytest.mark.parametrize("call", [lambda s: s.seal("west"), lambda s: s.unseal("west")])
def test_seal_and_unseal_of_a_silo_not_in_use_raise_key_error(silos, call):
    with pytest.raises(KeyError):
        call(silos)
    assert silos.get_sealed() == []


def test_silo_sealed_is_a_silo_error():
    assert issubclass(SiloSealed, SiloError)


def test_sealing_moves_no_grain(silos):
    before = state(silos)
    silos.seal("north")
    assert state(silos) == before


# --- what a seal blocks -------------------------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.load("north", "wheat", 1),
        lambda s: s.load("north", "oats", 1),
        lambda s: s.unload("north", "wheat", 1),
        lambda s: s.blend_into("north", "east"),
        lambda s: s.blend_into("south", "north"),
        lambda s: s.demolish_silo("north", "east"),
        lambda s: s.demolish_silo("south", "north"),
    ],
    ids=["load", "load_new_grain", "unload", "blend_out", "blend_in", "demolish_sealed", "demolish_into_sealed"],
)
def test_calls_naming_a_sealed_silo_raise(silos, call):
    silos.seal("north")
    before = state(silos)
    with pytest.raises(SiloSealed):
        call(silos)
    assert state(silos) == before
    assert silos.get_silos() == ["north", "south", "east"]


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.blend_into("east", "north"),
        lambda s: s.blend_into("north", "east"),
        lambda s: s.demolish_silo("east", "north"),
        lambda s: s.demolish_silo("north", "east"),
    ],
    ids=["blend_from_empty", "blend_empty_sealed", "demolish_empty", "demolish_into_empty"],
)
def test_calls_that_would_move_nothing_still_raise(silos, call):
    silos.seal("east")
    silos.seal("north")
    silos.unseal("north")
    before = state(silos)
    with pytest.raises(SiloSealed):
        call(silos)
    assert state(silos) == before
    assert silos.get_silos() == ["north", "south", "east"]


def test_other_silos_work_as_before(silos):
    silos.seal("north")
    silos.load("east", "corn", 5)
    silos.unload("south", "rye", 10)
    assert silos.blend_into("south", "east") == 30
    assert silos.demolish_silo("south", "east") == 0
    assert state(silos) == [
        ("north", [("barley", 20), ("wheat", 30)]),
        ("east", [("corn", 5), ("rye", 30)]),
    ]


def test_get_methods_work_on_sealed_silos(silos):
    silos.seal("north")
    assert silos.get_tonnes("north", "wheat") == 30
    assert silos.get_grains("north") == ["barley", "wheat"]
    assert silos.get_silos() == ["north", "south", "east"]


# --- unsealing --------------------------------------------------------------------


def test_after_unseal_everything_works_again(silos):
    silos.seal("north")
    silos.unseal("north")
    silos.load("north", "oats", 2)
    silos.unload("north", "wheat", 10)
    assert silos.blend_into("south", "north") == 40
    assert silos.demolish_silo("north", "east") == 82
    assert state(silos) == [
        ("south", []),
        ("east", [("barley", 20), ("oats", 2), ("rye", 40), ("wheat", 20)]),
    ]
