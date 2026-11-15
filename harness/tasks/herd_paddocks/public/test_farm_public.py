"""Public checks for farm.py.

Usage (with farm.py importable, e.g. in the sandbox):
    python -m pytest public/test_farm_public.py
"""

import pytest
from farm import Farm, NotEnoughAnimals


@pytest.fixture
def farm():
    f = Farm()
    f.add_paddock("north")
    f.add_paddock("south")
    return f


def test_arrivals_and_departures_change_the_count(farm):
    farm.arrive("north", "sheep", 5)
    farm.arrive("north", "sheep", 2)
    farm.depart("north", "sheep", 3)
    assert farm.get_count("north", "sheep") == 4
    assert farm.get_count("north", "cow") == 0


def test_departing_more_than_are_there_raises(farm):
    farm.arrive("north", "sheep", 5)
    with pytest.raises(NotEnoughAnimals):
        farm.depart("north", "sheep", 6)
    assert farm.get_count("north", "sheep") == 5


def test_a_species_whose_animals_all_moved_away_is_not_listed(farm):
    farm.arrive("north", "sheep", 5)
    farm.arrive("north", "cow", 4)
    farm.move("cow", "north", "south", 4)
    assert farm.get_species("north") == ["sheep"]
    assert farm.get_species("south") == ["cow"]
    assert farm.get_count("north", "cow") == 0


def test_move_all_moves_every_species_and_returns_how_many(farm):
    farm.arrive("north", "sheep", 5)
    farm.arrive("north", "cow", 2)
    farm.arrive("south", "goat", 1)
    assert farm.move_all("north", "south") == 7
    assert farm.get_species("north") == []
    assert farm.get_species("south") == ["cow", "goat", "sheep"]
    assert farm.get_paddocks() == ["north", "south"]


def test_a_closed_paddock_is_gone(farm):
    farm.arrive("north", "sheep", 5)
    farm.arrive("south", "sheep", 1)
    assert farm.close_paddock("north", "south") == 5
    assert farm.get_paddocks() == ["south"]
    assert farm.get_count("south", "sheep") == 6
    with pytest.raises(KeyError):
        farm.get_count("north", "sheep")
    with pytest.raises(KeyError):
        farm.arrive("north", "sheep", 1)


def test_closing_an_empty_paddock_returns_0_and_frees_its_name(farm):
    assert farm.close_paddock("south", "north") == 0
    assert farm.get_paddocks() == ["north"]
    farm.add_paddock("south")
    assert farm.get_paddocks() == ["north", "south"]
    assert farm.get_species("south") == []
