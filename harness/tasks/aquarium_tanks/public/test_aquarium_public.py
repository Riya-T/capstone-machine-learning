"""Public checks for aquarium.py.

Usage (with aquarium.py importable, e.g. in the sandbox):
    python -m pytest public/test_aquarium_public.py
"""

import pytest
from aquarium import Aquarium, NotEnoughFish


@pytest.fixture
def aquarium():
    a = Aquarium()
    a.add_tank("reef")
    a.add_tank("lagoon")
    return a


def test_fish_put_in_and_taken_out_change_the_count(aquarium):
    aquarium.add_fish("reef", "tang", 5)
    aquarium.add_fish("reef", "tang", 2)
    aquarium.remove_fish("reef", "tang", 3)
    assert aquarium.get_count("reef", "tang") == 4
    assert aquarium.get_count("reef", "guppy") == 0


def test_taking_out_more_fish_than_there_are_raises(aquarium):
    aquarium.add_fish("reef", "tang", 5)
    with pytest.raises(NotEnoughFish):
        aquarium.remove_fish("reef", "tang", 6)
    assert aquarium.get_count("reef", "tang") == 5


def test_a_species_with_no_fish_left_is_not_listed(aquarium):
    aquarium.add_fish("reef", "clownfish", 2)
    aquarium.add_fish("reef", "tang", 4)
    aquarium.remove_fish("reef", "clownfish", 2)
    assert aquarium.get_species("reef") == ["tang"]
    assert aquarium.get_count("reef", "clownfish") == 0


def test_move_all_moves_every_species_and_returns_how_many(aquarium):
    aquarium.add_fish("reef", "clownfish", 2)
    aquarium.add_fish("reef", "tang", 5)
    aquarium.add_fish("lagoon", "angelfish", 1)
    assert aquarium.move_all("reef", "lagoon") == 7
    assert aquarium.get_species("reef") == []
    assert aquarium.get_species("lagoon") == ["angelfish", "clownfish", "tang"]
    assert aquarium.get_tanks() == ["reef", "lagoon"]


def test_a_drained_tank_is_gone(aquarium):
    aquarium.add_fish("reef", "tang", 5)
    aquarium.add_fish("lagoon", "guppy", 1)
    assert aquarium.drain_tank("reef", "lagoon") == 5
    assert aquarium.get_tanks() == ["lagoon"]
    assert aquarium.get_count("lagoon", "tang") == 5
    assert aquarium.get_count("lagoon", "guppy") == 1
    with pytest.raises(KeyError):
        aquarium.get_count("reef", "tang")
    with pytest.raises(KeyError):
        aquarium.add_fish("reef", "tang", 1)


def test_tanks_are_listed_in_the_order_added():
    a = Aquarium()
    for name in ["reef", "kelp", "lagoon"]:
        a.add_tank(name)
    assert a.get_tanks() == ["reef", "kelp", "lagoon"]
