"""Hidden tests for the c_allowed change (species allowed in a paddock).
Never shown to the writer or the editor.

Usage (with farm.py importable, e.g. in the sandbox):
    python -m pytest changes/c_allowed/private/test_allowed_new.py
"""

import pytest
from farm import Farm, FarmError, NotAllowed, NotEnoughAnimals

BAD_SETTINGS = ["sheep", 5, ["sheep", ""], ["sheep", None], [3]]


@pytest.fixture
def farm():
    # north holds cows, goats and sheep (added in that order, which is also
    # alphabetical), so goats are in the middle whichever order a program uses.
    f = Farm()
    for name in ["north", "south", "east"]:
        f.add_paddock(name)
    f.arrive("north", "cow", 3)
    f.arrive("north", "goat", 2)
    f.arrive("north", "sheep", 4)
    return f


def state(f):
    return [(p, [(s, f.get_count(p, s)) for s in f.get_species(p)]) for p in f.get_paddocks()]


# --- the setting ------------------------------------------------------------


def test_every_paddock_starts_allowing_any_species(farm):
    assert [farm.get_allowed(p) for p in farm.get_paddocks()] == [None, None, None]
    farm.add_paddock("west")
    assert farm.get_allowed("west") is None
    farm.arrive("west", "llama", 1)
    assert farm.get_count("west", "llama") == 1


def test_a_paddock_added_again_after_closing_allows_any_species(farm):
    farm.set_allowed("east", ["cow"])
    farm.close_paddock("east", "south")
    farm.add_paddock("east")
    assert farm.get_allowed("east") is None
    farm.arrive("east", "goat", 1)
    assert farm.get_count("east", "goat") == 1


def test_get_allowed_is_alphabetical_without_duplicates(farm):
    farm.set_allowed("south", ["sheep", "cow", "sheep", "alpaca"])
    assert farm.get_allowed("south") == ["alpaca", "cow", "sheep"]


def test_each_setting_replaces_the_one_before(farm):
    farm.set_allowed("south", ["cow"])
    farm.set_allowed("south", ["sheep"])
    assert farm.get_allowed("south") == ["sheep"]
    with pytest.raises(NotAllowed):
        farm.arrive("south", "cow", 1)
    farm.set_allowed("south", None)
    assert farm.get_allowed("south") is None
    farm.arrive("south", "cow", 1)
    assert farm.get_count("south", "cow") == 1


def test_an_empty_list_allows_no_species(farm):
    farm.set_allowed("south", [])
    assert farm.get_allowed("south") == []
    before = state(farm)
    with pytest.raises(NotAllowed):
        farm.arrive("south", "sheep", 1)
    with pytest.raises(NotAllowed):
        farm.move("sheep", "north", "south", 1)
    assert state(farm) == before


@pytest.mark.parametrize("setting", BAD_SETTINGS)
def test_invalid_settings_are_rejected_and_keep_the_old_one(farm, setting):
    farm.set_allowed("south", ["cow"])
    with pytest.raises(ValueError):
        farm.set_allowed("south", setting)
    assert farm.get_allowed("south") == ["cow"]


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.set_allowed("west", ["cow"]),
        lambda f: f.set_allowed("west", None),
        lambda f: f.get_allowed("west"),
        lambda f: f.set_allowed("west", "cow"),  # KeyError before ValueError
        lambda f: f.set_allowed("east", ["cow"]),  # closed below
        lambda f: f.get_allowed("east"),
    ],
)
def test_paddocks_not_in_use_raise_key_error(farm, call):
    farm.close_paddock("east", "south")
    with pytest.raises(KeyError):
        call(farm)


def test_a_setting_changes_no_counts(farm):
    before = state(farm)
    farm.set_allowed("north", ["pig"])
    farm.set_allowed("south", [])
    assert state(farm) == before


def test_a_setting_only_applies_to_its_own_paddock(farm):
    farm.set_allowed("south", ["cow"])
    farm.arrive("east", "goat", 1)
    farm.move("goat", "north", "east", 1)
    assert farm.get_count("east", "goat") == 2


# --- arrive and move ----------------------------------------------------------


def test_arrive_of_an_allowed_species_works(farm):
    farm.set_allowed("south", ["cow", "sheep"])
    farm.arrive("south", "sheep", 2)
    assert farm.get_count("south", "sheep") == 2


def test_arrive_of_a_refused_species_changes_nothing(farm):
    farm.set_allowed("south", ["cow", "sheep"])
    before = state(farm)
    with pytest.raises(NotAllowed):
        farm.arrive("south", "goat", 1)
    assert state(farm) == before


def test_move_into_a_paddock_that_allows_the_species(farm):
    farm.set_allowed("south", ["goat"])
    farm.move("goat", "north", "south", 2)
    assert farm.get_count("south", "goat") == 2
    assert farm.get_species("north") == ["cow", "sheep"]


def test_move_into_a_paddock_that_refuses_the_species_changes_nothing(farm):
    farm.set_allowed("south", ["cow", "sheep"])
    before = state(farm)
    with pytest.raises(NotAllowed):
        farm.move("goat", "north", "south", 1)
    assert state(farm) == before


# --- move_all and close_paddock ---------------------------------------------


def test_move_all_into_a_paddock_that_allows_every_species(farm):
    farm.set_allowed("south", ["sheep", "goat", "cow"])
    assert farm.move_all("north", "south") == 9
    assert farm.get_species("south") == ["cow", "goat", "sheep"]


def test_move_all_with_one_refused_species_moves_nothing(farm):
    farm.set_allowed("south", ["cow", "sheep"])
    before = state(farm)
    with pytest.raises(NotAllowed):
        farm.move_all("north", "south")
    assert state(farm) == before
    assert farm.get_count("north", "cow") == 3
    assert farm.get_count("south", "cow") == 0


def test_close_paddock_into_a_paddock_that_allows_every_species(farm):
    farm.set_allowed("south", ["cow", "goat", "sheep", "pig"])
    assert farm.close_paddock("north", "south") == 9
    assert farm.get_paddocks() == ["south", "east"]
    assert farm.get_count("south", "goat") == 2


def test_close_paddock_with_one_refused_species_moves_nothing_and_keeps_it(farm):
    farm.set_allowed("east", ["cow", "sheep"])
    before = state(farm)
    with pytest.raises(NotAllowed):
        farm.close_paddock("north", "east")
    assert state(farm) == before
    assert farm.get_paddocks() == ["north", "south", "east"]
    assert farm.get_count("east", "cow") == 0


def test_a_refused_close_can_be_retried_once_the_species_is_allowed(farm):
    farm.set_allowed("east", ["cow", "sheep"])
    with pytest.raises(NotAllowed):
        farm.close_paddock("north", "east")
    farm.set_allowed("east", ["cow", "goat", "sheep"])
    assert farm.close_paddock("north", "east") == 9
    assert farm.get_paddocks() == ["south", "east"]


def test_an_empty_paddock_never_raises_not_allowed(farm):
    farm.set_allowed("north", [])
    assert farm.move_all("south", "north") == 0
    assert farm.close_paddock("south", "north") == 0
    assert farm.get_paddocks() == ["north", "east"]


# --- animals already there --------------------------------------------------


def test_animals_already_in_a_paddock_are_not_affected(farm):
    farm.set_allowed("north", ["pig"])
    assert farm.get_count("north", "cow") == 3
    assert farm.get_species("north") == ["cow", "goat", "sheep"]
    farm.depart("north", "cow", 1)
    farm.move("goat", "north", "south", 2)
    assert farm.get_count("north", "cow") == 2
    assert farm.get_count("south", "goat") == 2
    with pytest.raises(NotAllowed):
        farm.arrive("north", "cow", 1)


def test_the_setting_of_the_paddock_animals_leave_is_not_checked(farm):
    farm.set_allowed("north", [])
    assert farm.move_all("north", "south") == 9
    farm.move("cow", "south", "east", 1)
    farm.set_allowed("south", [])
    assert farm.close_paddock("south", "east") == 8
    assert farm.get_count("east", "cow") == 3


def test_depart_never_checks_the_setting(farm):
    farm.set_allowed("north", [])
    farm.depart("north", "sheep", 4)
    assert farm.get_species("north") == ["cow", "goat"]


# --- order of errors ----------------------------------------------------------


def test_a_paddock_not_in_use_is_reported_before_not_allowed(farm):
    farm.set_allowed("south", [])
    with pytest.raises(KeyError):
        farm.move("cow", "south", "west", 1)
    with pytest.raises(KeyError):
        farm.move_all("north", "west")
    with pytest.raises(KeyError):
        farm.close_paddock("west", "south")


def test_a_bad_count_is_reported_before_not_allowed(farm):
    farm.set_allowed("south", [])
    before = state(farm)
    with pytest.raises(ValueError):
        farm.arrive("south", "cow", 0)
    with pytest.raises(ValueError):
        farm.arrive("south", "cow", -2)
    with pytest.raises(ValueError):
        farm.move("cow", "north", "south", 0)
    assert state(farm) == before


def test_the_same_paddock_is_reported_before_not_allowed(farm):
    farm.set_allowed("north", ["pig"])
    with pytest.raises(ValueError):
        farm.move("cow", "north", "north", 1)
    with pytest.raises(ValueError):
        farm.move_all("north", "north")
    with pytest.raises(ValueError):
        farm.close_paddock("north", "north")


def test_not_enough_animals_is_reported_before_not_allowed(farm):
    farm.set_allowed("south", ["pig"])
    before = state(farm)
    with pytest.raises(NotEnoughAnimals):
        farm.move("cow", "north", "south", 4)
    with pytest.raises(NotEnoughAnimals):
        farm.move("llama", "north", "south", 1)
    assert state(farm) == before


def test_not_allowed_is_a_farm_error_but_not_not_enough_animals():
    assert issubclass(NotAllowed, FarmError)
    assert not issubclass(NotAllowed, NotEnoughAnimals)
