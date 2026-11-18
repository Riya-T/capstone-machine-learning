"""Hidden tests for the tank capacity change. Never shown to the writer or
the editor.

Usage (with aquarium.py importable, e.g. in the sandbox):
    python -m pytest changes/c_capacity/private/test_capacity_new.py
"""

import pytest
from aquarium import Aquarium, AquariumError, NotEnoughFish, TankFull


@pytest.fixture
def aquarium():
    # reef holds 6 of at most 8, lagoon has no limit, kelp holds 0 of at most 4.
    a = Aquarium()
    a.add_tank("reef", capacity=8)
    a.add_tank("lagoon")
    a.add_tank("kelp", capacity=4)
    a.add_fish("reef", "tang", 4)
    a.add_fish("reef", "clownfish", 2)
    a.add_fish("lagoon", "guppy", 3)
    return a


def state(a):
    return [(t, [(s, a.get_count(t, s)) for s in a.get_species(t)]) for t in a.get_tanks()]


# --- the capacity -------------------------------------------------------------


def test_get_capacity_returns_the_capacity_or_none(aquarium):
    assert [aquarium.get_capacity(t) for t in aquarium.get_tanks()] == [8, None, 4]


def test_a_tank_added_without_a_capacity_has_no_limit(aquarium):
    aquarium.add_tank("arctic")
    assert aquarium.get_capacity("arctic") is None
    aquarium.add_fish("arctic", "cod", 500)
    assert aquarium.get_count("arctic", "cod") == 500


@pytest.mark.parametrize("capacity", [0, -2])
def test_a_capacity_of_0_or_less_adds_no_tank(aquarium, capacity):
    before = state(aquarium)
    with pytest.raises(ValueError):
        aquarium.add_tank("arctic", capacity=capacity)
    assert state(aquarium) == before
    aquarium.add_tank("arctic", capacity=3)
    assert aquarium.get_capacity("arctic") == 3


def test_get_capacity_of_a_tank_not_in_use_raises_key_error(aquarium):
    with pytest.raises(KeyError):
        aquarium.get_capacity("arctic")
    aquarium.drain_tank("kelp", "lagoon")
    with pytest.raises(KeyError):
        aquarium.get_capacity("kelp")


def test_tank_full_is_an_aquarium_error_but_not_not_enough_fish():
    assert issubclass(TankFull, AquariumError)
    assert not issubclass(TankFull, NotEnoughFish)


# --- add_fish -------------------------------------------------------------------


def test_add_fish_up_to_exactly_the_capacity(aquarium):
    aquarium.add_fish("reef", "seahorse", 2)
    assert aquarium.get_count("reef", "seahorse") == 2


def test_add_fish_counts_every_species_together(aquarium):
    before = state(aquarium)
    with pytest.raises(TankFull):
        aquarium.add_fish("reef", "seahorse", 3)
    with pytest.raises(TankFull):
        aquarium.add_fish("reef", "tang", 3)
    assert state(aquarium) == before


def test_taking_fish_out_makes_room(aquarium):
    aquarium.remove_fish("reef", "tang", 3)
    aquarium.add_fish("reef", "seahorse", 5)
    assert aquarium.get_count("reef", "seahorse") == 5


def test_remove_fish_works_in_a_full_tank(aquarium):
    aquarium.add_fish("kelp", "seahorse", 4)
    aquarium.remove_fish("kelp", "seahorse", 4)
    assert aquarium.get_species("kelp") == []


# --- move_all and drain_tank ----------------------------------------------------


def test_move_all_into_a_tank_with_room(aquarium):
    aquarium.remove_fish("lagoon", "guppy", 1)
    assert aquarium.move_all("lagoon", "reef") == 2
    assert aquarium.get_count("reef", "guppy") == 2
    assert aquarium.get_species("lagoon") == []


def test_move_all_that_would_overfill_moves_nothing(aquarium):
    before = state(aquarium)
    with pytest.raises(TankFull):
        aquarium.move_all("lagoon", "reef")
    assert state(aquarium) == before
    with pytest.raises(TankFull):
        aquarium.move_all("reef", "kelp")
    assert state(aquarium) == before


def test_drain_tank_into_a_tank_with_room(aquarium):
    assert aquarium.drain_tank("lagoon", "kelp") == 3
    assert aquarium.get_tanks() == ["reef", "kelp"]
    assert aquarium.get_count("kelp", "guppy") == 3


def test_drain_tank_that_would_overfill_moves_nothing_and_keeps_the_tank(aquarium):
    before = state(aquarium)
    with pytest.raises(TankFull):
        aquarium.drain_tank("reef", "kelp")
    assert state(aquarium) == before
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]
    assert aquarium.get_count("kelp", "tang") == 0


def test_the_capacity_of_the_tank_the_fish_leave_is_not_checked(aquarium):
    aquarium.add_fish("kelp", "seahorse", 4)
    assert aquarium.move_all("kelp", "lagoon") == 4
    assert aquarium.drain_tank("reef", "lagoon") == 6
    assert aquarium.get_count("lagoon", "seahorse") == 4


def test_a_name_added_again_gets_its_own_capacity(aquarium):
    aquarium.drain_tank("kelp", "lagoon")
    aquarium.add_tank("kelp")
    assert aquarium.get_capacity("kelp") is None
    aquarium.add_fish("kelp", "seahorse", 9)
    aquarium.drain_tank("reef", "lagoon")
    aquarium.add_tank("reef", capacity=2)
    assert aquarium.get_capacity("reef") == 2
    with pytest.raises(TankFull):
        aquarium.add_fish("reef", "tang", 3)


# --- undo -----------------------------------------------------------------------


def test_an_undone_drain_brings_the_tank_back_with_its_capacity(aquarium):
    aquarium.drain_tank("kelp", "lagoon")
    aquarium.undo()
    assert aquarium.get_capacity("kelp") == 4
    aquarium.add_fish("kelp", "seahorse", 4)
    with pytest.raises(TankFull):
        aquarium.add_fish("kelp", "seahorse", 1)


def test_an_undone_add_tank_frees_the_name_for_any_capacity(aquarium):
    aquarium.add_tank("arctic", capacity=1)
    aquarium.undo()
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]
    aquarium.add_tank("arctic", capacity=10)
    assert aquarium.get_capacity("arctic") == 10
    aquarium.add_fish("arctic", "cod", 10)
    assert aquarium.get_count("arctic", "cod") == 10


def test_undo_of_fish_put_in_makes_room_again(aquarium):
    aquarium.add_fish("reef", "seahorse", 2)
    aquarium.undo()
    aquarium.add_fish("reef", "tang", 2)
    assert aquarium.get_count("reef", "tang") == 6


def test_a_refused_call_is_not_undone(aquarium):
    aquarium.add_fish("kelp", "seahorse", 1)
    with pytest.raises(TankFull):
        aquarium.add_fish("kelp", "seahorse", 4)
    aquarium.undo()  # the first seahorse
    assert aquarium.get_species("kelp") == []
    assert aquarium.get_count("lagoon", "guppy") == 3
