"""Hidden tests for the initial garden_beds spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with garden.py importable, e.g. in the sandbox):
    python -m pytest private/test_garden_initial.py
"""

import pytest
from garden import Garden, GardenError, NotEnoughPlants


@pytest.fixture
def garden():
    g = Garden()
    for name in ["north", "south", "east"]:
        g.add_bed(name)
    g.plant("north", "rose", 5)
    g.plant("north", "tulip", 2)
    return g


def state(g):
    """Every bed in order with its species and counts, to check that a failed
    call changed nothing."""
    return [(b, [(s, g.get_count(b, s)) for s in g.get_species(b)]) for b in g.get_beds()]


# --- beds -----------------------------------------------------------------------


def test_a_new_bed_is_empty():
    g = Garden()
    g.add_bed("north")
    assert g.get_species("north") == []
    assert g.get_count("north", "rose") == 0


def test_beds_are_listed_in_the_order_added():
    g = Garden()
    for name in ["west", "north", "east"]:
        g.add_bed(name)
    assert g.get_beds() == ["west", "north", "east"]


def test_a_new_garden_has_no_beds():
    assert Garden().get_beds() == []


def test_adding_a_name_in_use_is_rejected(garden):
    before = state(garden)
    with pytest.raises(GardenError):
        garden.add_bed("north")
    assert state(garden) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.plant("west", "rose", 1),
        lambda g: g.pull("west", "rose", 1),
        lambda g: g.transplant_all("west", "south"),
        lambda g: g.transplant_all("north", "west"),
        lambda g: g.clear_bed("west", "south"),
        lambda g: g.clear_bed("north", "west"),
        lambda g: g.get_count("west", "rose"),
        lambda g: g.get_species("west"),
    ],
)
def test_beds_that_were_never_added_raise_key_error(garden, call):
    before = state(garden)
    with pytest.raises(KeyError):
        call(garden)
    assert state(garden) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.plant("east", "rose", 1),
        lambda g: g.pull("east", "rose", 1),
        lambda g: g.transplant_all("east", "north"),
        lambda g: g.transplant_all("north", "east"),
        lambda g: g.clear_bed("east", "north"),
        lambda g: g.clear_bed("north", "east"),
        lambda g: g.get_count("east", "rose"),
        lambda g: g.get_species("east"),
    ],
)
def test_a_cleared_bed_is_not_in_use(garden, call):
    garden.plant("east", "mint", 1)
    garden.clear_bed("east", "south")
    before = state(garden)
    with pytest.raises(KeyError):
        call(garden)
    assert state(garden) == before


# --- planting and pulling -----------------------------------------------------------


def test_planting_and_pulling_change_the_count(garden):
    garden.plant("north", "rose", 3)
    garden.pull("north", "rose", 6)
    garden.plant("south", "rose", 1)
    assert garden.get_count("north", "rose") == 2
    assert garden.get_count("south", "rose") == 1
    assert garden.get_count("north", "tulip") == 2


def test_every_plant_of_a_species_can_be_pulled(garden):
    garden.pull("north", "tulip", 2)
    assert garden.get_count("north", "tulip") == 0
    assert garden.get_species("north") == ["rose"]


def test_species_are_listed_in_alphabetical_order(garden):
    garden.plant("south", "tulip", 1)
    garden.plant("south", "fern", 2)
    garden.plant("south", "mint", 3)
    assert garden.get_species("south") == ["fern", "mint", "tulip"]


def test_pulling_more_than_there_are_raises_and_changes_nothing(garden):
    before = state(garden)
    with pytest.raises(NotEnoughPlants):
        garden.pull("north", "tulip", 3)
    with pytest.raises(NotEnoughPlants):
        garden.pull("north", "fern", 1)
    with pytest.raises(NotEnoughPlants):
        garden.pull("south", "rose", 1)
    assert state(garden) == before


@pytest.mark.parametrize("count", [0, -3])
def test_planting_a_count_of_0_or_less_is_rejected(garden, count):
    before = state(garden)
    with pytest.raises(ValueError):
        garden.plant("north", "rose", count)
    assert state(garden) == before


# --- transplanting and clearing -----------------------------------------------------


def test_transplant_all_moves_every_species(garden):
    garden.plant("south", "rose", 1)
    garden.plant("south", "fern", 4)
    assert garden.transplant_all("north", "south") == 7
    assert garden.get_species("north") == []
    assert garden.get_species("south") == ["fern", "rose", "tulip"]
    assert garden.get_count("south", "rose") == 6
    assert garden.get_count("south", "tulip") == 2
    assert garden.get_beds() == ["north", "south", "east"]


def test_a_bed_emptied_by_transplant_all_can_be_planted_again(garden):
    garden.transplant_all("north", "east")
    garden.plant("north", "fern", 3)
    assert garden.get_species("north") == ["fern"]
    assert garden.get_count("east", "rose") == 5


def test_transplant_all_from_an_empty_bed_moves_nothing(garden):
    before = state(garden)
    assert garden.transplant_all("east", "north") == 0
    assert state(garden) == before


def test_clear_bed_moves_every_plant_and_removes_the_bed(garden):
    garden.plant("east", "rose", 2)
    assert garden.clear_bed("north", "east") == 7
    assert garden.get_beds() == ["south", "east"]
    assert garden.get_count("east", "rose") == 7
    assert garden.get_count("east", "tulip") == 2


def test_clearing_into_an_empty_bed(garden):
    assert garden.clear_bed("north", "south") == 7
    assert garden.get_beds() == ["south", "east"]
    assert garden.get_species("south") == ["rose", "tulip"]


def test_the_other_beds_keep_their_order_after_a_clear(garden):
    garden.add_bed("west")
    garden.plant("south", "fern", 1)
    garden.clear_bed("south", "west")
    assert garden.get_beds() == ["north", "east", "west"]
    assert garden.get_count("west", "fern") == 1


@pytest.mark.parametrize(
    "call",
    [
        lambda g: g.transplant_all("north", "north"),
        lambda g: g.clear_bed("north", "north"),
        lambda g: g.transplant_all("east", "east"),
    ],
    ids=["transplant_all", "clear_bed", "transplant_all_empty"],
)
def test_the_same_bed_on_both_sides_is_rejected(garden, call):
    before = state(garden)
    with pytest.raises(ValueError):
        call(garden)
    assert state(garden) == before


# --- general ------------------------------------------------------------------------


def test_not_enough_plants_is_a_garden_error():
    assert issubclass(NotEnoughPlants, GardenError)


def test_gardens_do_not_share_beds():
    first, second = Garden(), Garden()
    first.add_bed("north")
    first.plant("north", "rose", 3)
    assert second.get_beds() == []
    second.add_bed("north")
    assert second.get_count("north", "rose") == 0
