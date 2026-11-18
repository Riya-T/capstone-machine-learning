"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor. They call only the spec's methods and undo, since they run in
both sequences.

Usage (with garden.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from garden import Garden, GardenError, NotEnoughPlants


@pytest.fixture
def garden():
    g = Garden()
    for name in ["north", "south", "east"]:
        g.add_bed(name)
    g.plant("north", "rose", 3)
    g.plant("north", "tulip", 2)
    g.plant("south", "fern", 4)
    return g


def state(g):
    return [(b, [(s, g.get_count(b, s)) for s in g.get_species(b)]) for b in g.get_beds()]


# --- each call can be undone ----------------------------------------------------


def test_undo_of_planting_a_new_species(garden):
    before = state(garden)
    garden.plant("east", "mint", 2)
    garden.undo()
    assert state(garden) == before
    assert garden.get_species("east") == []


def test_undo_of_planting_more_of_a_species(garden):
    garden.plant("north", "rose", 5)
    garden.undo()
    assert garden.get_count("north", "rose") == 3


def test_undo_of_a_pull(garden):
    before = state(garden)
    garden.pull("north", "rose", 1)
    garden.undo()
    assert state(garden) == before


def test_undo_of_pulling_every_plant_of_a_species(garden):
    before = state(garden)
    garden.pull("north", "tulip", 2)
    garden.undo()
    assert state(garden) == before
    assert garden.get_species("north") == ["rose", "tulip"]


def test_one_undo_takes_back_a_whole_transplant_all(garden):
    before = state(garden)
    assert garden.transplant_all("north", "south") == 5
    garden.undo()
    assert state(garden) == before
    assert garden.get_species("south") == ["fern"]


def test_undo_of_a_transplant_all_into_an_empty_bed(garden):
    before = state(garden)
    garden.transplant_all("south", "east")
    garden.undo()
    assert state(garden) == before
    assert garden.get_species("east") == []


def test_undo_of_a_transplant_all_onto_the_same_species(garden):
    garden.plant("east", "rose", 4)
    before = state(garden)
    garden.transplant_all("north", "east")
    assert garden.get_count("east", "rose") == 7
    garden.undo()
    assert state(garden) == before
    assert garden.get_count("east", "rose") == 4


def test_undo_of_clear_bed_brings_it_back_with_its_plants(garden):
    before = state(garden)
    assert garden.clear_bed("north", "east") == 5
    garden.undo()
    assert state(garden) == before
    assert garden.get_beds() == ["north", "south", "east"]
    assert garden.get_count("east", "rose") == 0


def test_undo_of_clear_bed_puts_it_back_at_its_place_in_the_list(garden):
    garden.add_bed("west")
    before = state(garden)
    garden.clear_bed("south", "west")
    assert garden.get_beds() == ["north", "east", "west"]
    garden.undo()
    assert garden.get_beds() == ["north", "south", "east", "west"]
    assert state(garden) == before


def test_a_bed_brought_back_is_in_use_again(garden):
    garden.clear_bed("north", "east")
    garden.undo()
    garden.plant("north", "rose", 1)
    assert garden.get_count("north", "rose") == 4
    with pytest.raises(GardenError):
        garden.add_bed("north")
    assert garden.clear_bed("north", "south") == 6
    assert garden.get_beds() == ["south", "east"]


def test_undo_of_add_bed_removes_it_and_frees_the_name(garden):
    garden.add_bed("west")
    garden.undo()
    assert garden.get_beds() == ["north", "south", "east"]
    with pytest.raises(KeyError):
        garden.get_species("west")
    garden.add_bed("west")
    assert garden.get_beds() == ["north", "south", "east", "west"]
    assert garden.get_species("west") == []


def test_undoing_two_clears_in_a_row_restores_the_order(garden):
    before = state(garden)
    garden.clear_bed("north", "east")
    garden.clear_bed("south", "east")
    assert garden.get_beds() == ["east"]
    garden.undo()
    assert garden.get_beds() == ["south", "east"]
    assert garden.get_count("east", "fern") == 0
    assert garden.get_count("east", "rose") == 3
    garden.undo()
    assert state(garden) == before


# --- calls that move nothing ----------------------------------------------------


def test_a_transplant_all_of_nothing_is_still_a_call(garden):
    garden.plant("east", "mint", 1)
    garden.pull("east", "mint", 1)
    assert garden.transplant_all("east", "north") == 0
    garden.undo()  # the transplant_all, which changed nothing
    assert garden.get_species("east") == []
    garden.undo()  # the pull
    assert garden.get_count("east", "mint") == 1


def test_undo_of_a_clear_after_a_transplant_all_of_nothing(garden):
    garden.plant("south", "fern", 1)
    assert garden.transplant_all("east", "south") == 0
    assert garden.clear_bed("south", "north") == 5
    garden.undo()
    assert garden.get_beds() == ["north", "south", "east"]
    assert garden.get_count("south", "fern") == 5
    assert garden.get_count("north", "fern") == 0
    garden.undo()  # the transplant_all of nothing
    assert garden.get_count("south", "fern") == 5
    garden.undo()
    assert garden.get_count("south", "fern") == 4


# --- what is and is not recorded --------------------------------------------------


def test_each_undo_goes_one_call_further_back():
    g = Garden()
    calls = [
        lambda: g.add_bed("north"),
        lambda: g.add_bed("south"),
        lambda: g.plant("north", "rose", 5),
        lambda: g.plant("north", "tulip", 2),
        lambda: g.add_bed("east"),
        lambda: g.plant("south", "fern", 4),
        lambda: g.pull("north", "rose", 1),
        lambda: g.transplant_all("south", "east"),
        lambda: g.clear_bed("north", "east"),
        lambda: g.add_bed("west"),
        lambda: g.plant("west", "mint", 1),
        lambda: g.transplant_all("south", "west"),
        lambda: g.clear_bed("west", "south"),
    ]
    states = [state(g)]
    for call in calls:
        call()
        states.append(state(g))
    assert g.get_beds() == ["south", "east"]
    assert g.get_count("east", "rose") == 4
    assert g.get_count("south", "mint") == 1
    for expected in reversed(states[:-1]):
        g.undo()
        assert state(g) == expected
    with pytest.raises(GardenError):
        g.undo()
    assert g.get_beds() == []


def test_failed_calls_are_not_recorded(garden):
    garden.plant("east", "mint", 2)
    for call in (
        lambda: garden.pull("north", "rose", 99),
        lambda: garden.pull("east", "fern", 1),
        lambda: garden.transplant_all("north", "north"),
        lambda: garden.transplant_all("north", "west"),
        lambda: garden.clear_bed("south", "south"),
        lambda: garden.clear_bed("west", "south"),
        lambda: garden.add_bed("north"),
        lambda: garden.plant("west", "rose", 1),
        lambda: garden.plant("north", "rose", 0),
    ):
        with pytest.raises((ValueError, KeyError, GardenError)):
            call()
    garden.undo()  # the mint
    assert garden.get_species("east") == []
    assert garden.get_count("north", "rose") == 3


def test_get_calls_are_not_recorded(garden):
    garden.plant("east", "mint", 2)
    garden.get_count("east", "mint")
    garden.get_species("east")
    garden.get_beds()
    garden.undo()
    assert garden.get_species("east") == []
    assert garden.get_count("south", "fern") == 4


def test_there_is_no_redo():
    g = Garden()
    g.add_bed("north")
    g.plant("north", "rose", 3)
    g.undo()
    g.undo()
    assert g.get_beds() == []
    with pytest.raises(GardenError):
        g.undo()


def test_new_calls_after_an_undo_are_undone_first(garden):
    garden.plant("east", "mint", 2)
    garden.undo()
    garden.plant("east", "sage", 1)
    garden.undo()
    assert garden.get_species("east") == []
    garden.undo()  # the ferns planted in the fixture
    assert garden.get_species("south") == []
    assert garden.get_species("north") == ["rose", "tulip"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    g = Garden()
    with pytest.raises(GardenError):
        g.undo()
    g.add_bed("north")
    g.undo()
    with pytest.raises(GardenError):
        g.undo()
    assert g.get_beds() == []
    g.add_bed("north")
    g.plant("north", "rose", 1)
    assert g.get_count("north", "rose") == 1


def test_the_whole_fixture_can_be_undone(garden):
    for _ in range(6):
        garden.undo()
    assert garden.get_beds() == []
    with pytest.raises(GardenError):
        garden.undo()


def test_undo_restores_counts_that_a_later_call_checks(garden):
    garden.pull("north", "rose", 3)
    garden.undo()
    assert garden.transplant_all("north", "east") == 5
    with pytest.raises(NotEnoughPlants):
        garden.pull("north", "rose", 1)
    assert garden.get_count("east", "rose") == 3
