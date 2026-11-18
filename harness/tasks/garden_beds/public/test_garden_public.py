"""Public checks for garden.py.

Usage (with garden.py importable, e.g. in the sandbox):
    python -m pytest public/test_garden_public.py
"""

import pytest
from garden import Garden, NotEnoughPlants


@pytest.fixture
def garden():
    g = Garden()
    g.add_bed("north")
    g.add_bed("south")
    return g


def test_planting_and_pulling_change_the_count(garden):
    garden.plant("north", "rose", 5)
    garden.plant("north", "rose", 2)
    garden.pull("north", "rose", 3)
    assert garden.get_count("north", "rose") == 4
    assert garden.get_count("north", "fern") == 0


def test_pulling_more_than_there_are_raises(garden):
    garden.plant("north", "rose", 5)
    with pytest.raises(NotEnoughPlants):
        garden.pull("north", "rose", 6)
    assert garden.get_count("north", "rose") == 5


def test_species_are_listed_alphabetically_and_only_while_they_grow(garden):
    garden.plant("north", "tulip", 2)
    garden.plant("north", "fern", 1)
    garden.plant("north", "mint", 4)
    garden.pull("north", "fern", 1)
    assert garden.get_species("north") == ["mint", "tulip"]


def test_transplant_all_moves_every_species_and_returns_how_many(garden):
    garden.plant("north", "rose", 5)
    garden.plant("north", "tulip", 2)
    garden.plant("south", "fern", 1)
    assert garden.transplant_all("north", "south") == 7
    assert garden.get_species("north") == []
    assert garden.get_species("south") == ["fern", "rose", "tulip"]
    assert garden.get_beds() == ["north", "south"]


def test_a_cleared_bed_is_gone(garden):
    garden.plant("north", "rose", 5)
    garden.plant("south", "rose", 1)
    assert garden.clear_bed("north", "south") == 5
    assert garden.get_beds() == ["south"]
    assert garden.get_count("south", "rose") == 6
    with pytest.raises(KeyError):
        garden.get_count("north", "rose")
    with pytest.raises(KeyError):
        garden.plant("north", "rose", 1)
