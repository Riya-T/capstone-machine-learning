"""Hidden tests for the c_lookup change (one species across the garden).
Never shown to the writer or the editor. They call only the spec's methods
and this change's own, never undo.

Usage (with garden.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lookup/private/test_lookup_new.py
"""

import pytest
from garden import Garden


@pytest.fixture
def garden():
    g = Garden()
    for name in ["north", "south", "east"]:
        g.add_bed(name)
    g.plant("east", "rose", 4)
    g.plant("north", "rose", 3)
    g.plant("north", "tulip", 2)
    g.plant("south", "fern", 5)
    return g


def state(g):
    return [(b, [(s, g.get_count(b, s)) for s in g.get_species(b)]) for b in g.get_beds()]


# --- get_beds_with ----------------------------------------------------------------


def test_beds_are_listed_in_the_order_they_were_added(garden):
    assert garden.get_beds_with("rose") == ["north", "east"]
    assert garden.get_beds_with("tulip") == ["north"]
    assert garden.get_beds_with("fern") == ["south"]


def test_bed_order_is_not_alphabetical():
    g = Garden()
    for name in ["west", "east", "north"]:
        g.add_bed(name)
        g.plant(name, "mint", 1)
    assert g.get_beds_with("mint") == ["west", "east", "north"]


def test_a_species_that_grows_nowhere_gives_an_empty_list(garden):
    assert garden.get_beds_with("mint") == []
    assert Garden().get_beds_with("rose") == []


def test_a_bed_whose_plants_were_all_pulled_is_not_listed(garden):
    garden.pull("north", "rose", 3)
    assert garden.get_beds_with("rose") == ["east"]
    garden.plant("south", "rose", 1)
    assert garden.get_beds_with("rose") == ["south", "east"]


def test_get_beds_with_after_a_transplant_all(garden):
    garden.transplant_all("north", "south")
    assert garden.get_beds_with("rose") == ["south", "east"]
    assert garden.get_beds_with("tulip") == ["south"]


def test_a_cleared_bed_is_never_listed(garden):
    garden.clear_bed("east", "north")
    assert garden.get_beds_with("rose") == ["north"]
    garden.add_bed("west")
    garden.plant("west", "rose", 1)
    assert garden.get_beds_with("rose") == ["north", "west"]


# --- get_total ----------------------------------------------------------------------


def test_get_total_adds_up_every_bed(garden):
    assert garden.get_total("rose") == 7
    assert garden.get_total("tulip") == 2
    assert garden.get_total("fern") == 5


def test_get_total_of_a_species_that_grows_nowhere_is_0(garden):
    assert garden.get_total("mint") == 0
    garden.pull("north", "tulip", 2)
    assert garden.get_total("tulip") == 0


def test_get_total_follows_planting_and_pulling(garden):
    garden.plant("south", "rose", 2)
    garden.pull("east", "rose", 1)
    assert garden.get_total("rose") == 8


def test_moving_plants_does_not_change_the_total(garden):
    garden.transplant_all("north", "east")
    assert garden.get_total("rose") == 7
    garden.clear_bed("east", "south")
    assert garden.get_total("rose") == 7
    assert garden.get_total("tulip") == 2
    assert garden.get_beds_with("rose") == ["south"]


# --- nothing changes ----------------------------------------------------------------


def test_lookups_change_nothing(garden):
    before = state(garden)
    garden.get_beds_with("rose")
    garden.get_beds_with("mint")
    garden.get_total("rose")
    garden.get_total("mint")
    assert state(garden) == before
    assert garden.get_species("north") == ["rose", "tulip"]
