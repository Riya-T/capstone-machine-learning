"""Public checks for cellar.py.

Usage (with cellar.py importable, e.g. in the sandbox):
    python -m pytest public/test_cellar_public.py
"""

import pytest
from cellar import Cellar, NotEnoughBottles


@pytest.fixture
def cellar():
    c = Cellar()
    c.add_rack("north")
    c.add_rack("south")
    return c


def test_storing_and_taking_change_the_count(cellar):
    cellar.store("north", 2015, 6)
    cellar.store("north", 2015, 2)
    cellar.take("north", 2015, 3)
    assert cellar.get_count("north", 2015) == 5
    assert cellar.get_count("north", 2018) == 0


def test_taking_more_than_there_are_raises(cellar):
    cellar.store("north", 2015, 6)
    with pytest.raises(NotEnoughBottles):
        cellar.take("north", 2015, 7)
    assert cellar.get_count("north", 2015) == 6


def test_vintages_are_listed_oldest_first(cellar):
    cellar.store("north", 2018, 1)
    cellar.store("north", 2009, 4)
    cellar.store("north", 2015, 2)
    assert cellar.get_vintages("north") == [2009, 2015, 2018]


def test_relocate_all_moves_every_vintage_and_returns_how_many(cellar):
    cellar.store("north", 2015, 6)
    cellar.store("north", 2018, 2)
    cellar.store("south", 2015, 1)
    assert cellar.relocate_all("north", "south") == 8
    assert cellar.get_count("north", 2015) == 0
    assert cellar.get_count("north", 2018) == 0
    assert cellar.get_count("south", 2015) == 7
    assert cellar.get_racks() == ["north", "south"]


def test_a_decommissioned_rack_is_gone(cellar):
    cellar.store("north", 2015, 6)
    assert cellar.decommission_rack("north", "south") == 6
    assert cellar.get_racks() == ["south"]
    assert cellar.get_count("south", 2015) == 6
    with pytest.raises(KeyError):
        cellar.get_count("north", 2015)


def test_decommissioning_an_empty_rack_returns_0_and_frees_its_name(cellar):
    assert cellar.decommission_rack("south", "north") == 0
    cellar.add_rack("south")
    assert cellar.get_racks() == ["north", "south"]
    assert cellar.get_vintages("south") == []
