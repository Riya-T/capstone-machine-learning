"""Hidden tests for the initial herd_paddocks spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with farm.py importable, e.g. in the sandbox):
    python -m pytest private/test_farm_initial.py
"""

import pytest
from farm import Farm, FarmError, NotEnoughAnimals

BAD_COUNTS = [0, -3]


@pytest.fixture
def farm():
    f = Farm()
    for name in ["north", "south", "east"]:
        f.add_paddock(name)
    f.arrive("north", "sheep", 5)
    f.arrive("north", "cow", 2)
    return f


def state(f):
    """Every paddock in order with its species and counts, to check that a
    failed call changed nothing."""
    return [(p, [(s, f.get_count(p, s)) for s in f.get_species(p)]) for p in f.get_paddocks()]


# --- paddocks ---------------------------------------------------------------


def test_a_new_paddock_is_empty():
    f = Farm()
    f.add_paddock("north")
    assert f.get_species("north") == []
    assert f.get_count("north", "sheep") == 0


def test_paddocks_are_listed_in_the_order_added():
    f = Farm()
    for name in ["west", "north", "east"]:
        f.add_paddock(name)
    assert f.get_paddocks() == ["west", "north", "east"]


def test_adding_a_name_in_use_is_rejected(farm):
    before = state(farm)
    with pytest.raises(FarmError):
        farm.add_paddock("north")
    assert state(farm) == before


def test_a_closed_name_can_be_added_again_as_a_new_empty_paddock(farm):
    farm.close_paddock("north", "east")
    farm.add_paddock("north")
    assert farm.get_paddocks() == ["south", "east", "north"]
    assert farm.get_species("north") == []
    assert farm.get_count("north", "sheep") == 0
    assert farm.get_count("east", "sheep") == 5


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.arrive("west", "sheep", 1),
        lambda f: f.depart("west", "sheep", 1),
        lambda f: f.move("sheep", "west", "south", 1),
        lambda f: f.move("sheep", "north", "west", 1),
        lambda f: f.move_all("west", "south"),
        lambda f: f.move_all("north", "west"),
        lambda f: f.close_paddock("west", "south"),
        lambda f: f.close_paddock("north", "west"),
        lambda f: f.get_count("west", "sheep"),
        lambda f: f.get_species("west"),
    ],
)
def test_paddocks_that_are_not_in_use_raise_key_error(farm, call):
    before = state(farm)
    with pytest.raises(KeyError):
        call(farm)
    assert state(farm) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.arrive("east", "sheep", 1),
        lambda f: f.depart("east", "sheep", 1),
        lambda f: f.move("sheep", "east", "north", 1),
        lambda f: f.move("sheep", "north", "east", 1),
        lambda f: f.move_all("east", "north"),
        lambda f: f.move_all("north", "east"),
        lambda f: f.close_paddock("east", "north"),
        lambda f: f.close_paddock("north", "east"),
        lambda f: f.get_count("east", "sheep"),
        lambda f: f.get_species("east"),
    ],
)
def test_a_closed_paddock_is_not_in_use(farm, call):
    farm.close_paddock("east", "south")  # east is empty
    before = state(farm)
    with pytest.raises(KeyError):
        call(farm)
    assert state(farm) == before


# --- arriving and departing -------------------------------------------------


def test_arrivals_and_departures_change_the_count(farm):
    farm.arrive("north", "sheep", 3)
    farm.depart("north", "sheep", 6)
    farm.arrive("south", "sheep", 1)
    assert farm.get_count("north", "sheep") == 2
    assert farm.get_count("south", "sheep") == 1
    assert farm.get_count("north", "cow") == 2


def test_every_animal_of_a_species_can_depart(farm):
    farm.depart("north", "cow", 2)
    assert farm.get_count("north", "cow") == 0
    assert farm.get_species("north") == ["sheep"]


def test_departing_more_than_there_are_raises_and_changes_nothing(farm):
    before = state(farm)
    with pytest.raises(NotEnoughAnimals):
        farm.depart("north", "cow", 3)
    with pytest.raises(NotEnoughAnimals):
        farm.depart("north", "goat", 1)
    with pytest.raises(NotEnoughAnimals):
        farm.depart("south", "sheep", 1)
    assert state(farm) == before


# --- moving -----------------------------------------------------------------


def test_move_moves_animals_of_one_species(farm):
    farm.arrive("south", "sheep", 1)
    farm.move("sheep", "north", "south", 4)
    assert farm.get_count("north", "sheep") == 1
    assert farm.get_count("south", "sheep") == 5
    assert farm.get_count("north", "cow") == 2
    assert farm.get_count("south", "cow") == 0


def test_moving_every_animal_of_a_species_empties_it(farm):
    farm.move("cow", "north", "east", 2)
    assert farm.get_species("north") == ["sheep"]
    assert farm.get_species("east") == ["cow"]


def test_moving_more_than_there_are_raises_and_changes_nothing(farm):
    before = state(farm)
    with pytest.raises(NotEnoughAnimals):
        farm.move("cow", "north", "south", 3)
    with pytest.raises(NotEnoughAnimals):
        farm.move("goat", "north", "south", 1)
    with pytest.raises(NotEnoughAnimals):
        farm.move("sheep", "south", "north", 1)
    assert state(farm) == before


def test_move_all_moves_every_species(farm):
    farm.arrive("south", "sheep", 1)
    farm.arrive("south", "pig", 4)
    assert farm.move_all("north", "south") == 7
    assert farm.get_species("north") == []
    assert farm.get_species("south") == ["cow", "pig", "sheep"]
    assert farm.get_count("south", "sheep") == 6
    assert farm.get_count("south", "cow") == 2
    assert farm.get_paddocks() == ["north", "south", "east"]


def test_move_all_from_an_empty_paddock_moves_nothing(farm):
    before = state(farm)
    assert farm.move_all("east", "north") == 0
    assert state(farm) == before


def test_close_paddock_moves_every_animal_and_closes_it(farm):
    farm.arrive("east", "sheep", 2)
    assert farm.close_paddock("north", "east") == 7
    assert farm.get_paddocks() == ["south", "east"]
    assert farm.get_count("east", "sheep") == 7
    assert farm.get_count("east", "cow") == 2


def test_closing_an_empty_paddock_moves_nothing(farm):
    assert farm.close_paddock("south", "north") == 0
    assert farm.get_paddocks() == ["north", "east"]
    assert farm.get_count("north", "sheep") == 5


def test_the_other_paddocks_keep_their_order_after_a_close(farm):
    farm.add_paddock("west")
    farm.close_paddock("south", "west")
    assert farm.get_paddocks() == ["north", "east", "west"]


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.move("sheep", "north", "north", 1),
        lambda f: f.move_all("north", "north"),
        lambda f: f.close_paddock("north", "north"),
        lambda f: f.move_all("east", "east"),
    ],
    ids=["move", "move_all", "close_paddock", "move_all_empty"],
)
def test_the_same_paddock_on_both_sides_is_rejected(farm, call):
    before = state(farm)
    with pytest.raises(ValueError):
        call(farm)
    assert state(farm) == before


# --- counts -------------------------------------------------------------------


@pytest.mark.parametrize("count", BAD_COUNTS)
@pytest.mark.parametrize(
    "call",
    [
        lambda f, c: f.arrive("north", "sheep", c),
        lambda f, c: f.depart("north", "sheep", c),
        lambda f, c: f.move("sheep", "north", "south", c),
    ],
    ids=["arrive", "depart", "move"],
)
def test_counts_of_0_or_less_are_rejected(farm, call, count):
    before = state(farm)
    with pytest.raises(ValueError):
        call(farm, count)
    assert state(farm) == before


# --- order of errors ----------------------------------------------------------


def test_a_paddock_not_in_use_is_reported_before_missing_animals(farm):
    with pytest.raises(KeyError):
        farm.depart("west", "sheep", 99)
    with pytest.raises(KeyError):
        farm.move("sheep", "west", "south", 99)
    with pytest.raises(KeyError):
        farm.move("goat", "north", "west", 1)


def test_a_bad_count_is_reported_before_missing_animals(farm):
    # north has no goats, so each of these also asks for too many animals.
    with pytest.raises(ValueError):
        farm.depart("north", "goat", 0)
    with pytest.raises(ValueError):
        farm.move("goat", "north", "south", -1)


def test_the_same_paddock_is_reported_before_missing_animals(farm):
    with pytest.raises(ValueError):
        farm.move("sheep", "north", "north", 99)


# --- general ----------------------------------------------------------------


def test_not_enough_animals_is_a_farm_error():
    assert issubclass(NotEnoughAnimals, FarmError)


def test_farms_do_not_share_paddocks():
    first, second = Farm(), Farm()
    first.add_paddock("north")
    first.arrive("north", "sheep", 3)
    assert second.get_paddocks() == []
    second.add_paddock("north")
    assert second.get_count("north", "sheep") == 0
