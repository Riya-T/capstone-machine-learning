"""Hidden tests for the c_undo change (undo). Never shown to the writer or
the editor.

Usage (with farm.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_undo_new.py
"""

import pytest
from farm import Farm, FarmError, NotEnoughAnimals


@pytest.fixture
def farm():
    f = Farm()
    for name in ["north", "south", "east"]:
        f.add_paddock(name)
    f.arrive("north", "cow", 3)
    f.arrive("north", "goat", 2)
    f.arrive("south", "sheep", 4)
    return f


def state(f):
    return [(p, [(s, f.get_count(p, s)) for s in f.get_species(p)]) for p in f.get_paddocks()]


# --- each call can be undone ------------------------------------------------


def test_undo_of_an_arrival_of_a_new_species(farm):
    before = state(farm)
    farm.arrive("east", "pig", 2)
    farm.undo()
    assert state(farm) == before
    assert farm.get_species("east") == []


def test_undo_of_an_arrival_of_more_of_a_species(farm):
    farm.arrive("north", "cow", 5)
    farm.undo()
    assert farm.get_count("north", "cow") == 3


def test_undo_of_a_departure(farm):
    before = state(farm)
    farm.depart("north", "cow", 1)
    farm.undo()
    assert state(farm) == before


def test_undo_of_a_departure_of_every_animal_of_a_species(farm):
    before = state(farm)
    farm.depart("north", "goat", 2)
    farm.undo()
    assert state(farm) == before
    assert farm.get_species("north") == ["cow", "goat"]


def test_undo_of_a_move_restores_both_paddocks(farm):
    before = state(farm)
    farm.move("cow", "north", "south", 3)
    farm.undo()
    assert state(farm) == before
    assert farm.get_species("south") == ["sheep"]


def test_undo_of_a_move_all_restores_both_paddocks(farm):
    before = state(farm)
    assert farm.move_all("north", "south") == 5
    farm.undo()
    assert state(farm) == before


def test_undo_of_a_move_all_into_an_empty_paddock(farm):
    before = state(farm)
    farm.move_all("south", "east")
    farm.undo()
    assert state(farm) == before
    assert farm.get_species("east") == []


def test_undo_of_close_paddock_brings_it_back_with_its_animals(farm):
    before = state(farm)
    assert farm.close_paddock("north", "east") == 5
    farm.undo()
    assert state(farm) == before
    assert farm.get_paddocks() == ["north", "south", "east"]
    assert farm.get_count("east", "cow") == 0


def test_undo_of_close_paddock_keeps_its_place_in_the_list(farm):
    farm.add_paddock("west")
    before = state(farm)
    farm.close_paddock("south", "west")
    assert farm.get_paddocks() == ["north", "east", "west"]
    farm.undo()
    assert farm.get_paddocks() == ["north", "south", "east", "west"]
    assert state(farm) == before


def test_a_paddock_brought_back_is_in_use_again(farm):
    farm.close_paddock("north", "east")
    farm.undo()
    farm.arrive("north", "cow", 1)
    assert farm.get_count("north", "cow") == 4
    with pytest.raises(FarmError):
        farm.add_paddock("north")
    assert farm.close_paddock("north", "south") == 6
    assert farm.get_paddocks() == ["south", "east"]


def test_undo_of_add_paddock_removes_it_and_frees_the_name(farm):
    farm.add_paddock("west")
    farm.undo()
    assert farm.get_paddocks() == ["north", "south", "east"]
    with pytest.raises(KeyError):
        farm.get_species("west")
    farm.add_paddock("west")
    assert farm.get_paddocks() == ["north", "south", "east", "west"]
    assert farm.get_species("west") == []


def test_undo_through_a_name_that_was_closed_and_added_again(farm):
    farm.add_paddock("west")
    farm.arrive("west", "pig", 2)
    farm.close_paddock("west", "east")
    farm.add_paddock("west")  # a new, empty west
    farm.arrive("west", "llama", 1)
    farm.undo()  # the llama
    farm.undo()  # the new west
    assert farm.get_paddocks() == ["north", "south", "east"]
    farm.undo()  # the close: the old west comes back with its pigs
    assert farm.get_paddocks() == ["north", "south", "east", "west"]
    assert farm.get_species("west") == ["pig"]
    assert farm.get_count("east", "pig") == 0
    farm.undo()  # the pigs
    farm.undo()  # the first west
    assert farm.get_paddocks() == ["north", "south", "east"]


# --- calls that move nothing ------------------------------------------------


def test_a_move_all_of_nothing_is_still_a_call(farm):
    farm.arrive("east", "pig", 1)
    farm.depart("east", "pig", 1)
    assert farm.move_all("east", "north") == 0
    farm.undo()  # the move_all, which changed nothing
    assert farm.get_species("east") == []
    farm.undo()  # the depart
    assert farm.get_count("east", "pig") == 1


def test_closing_an_empty_paddock_can_be_undone(farm):
    farm.arrive("south", "sheep", 1)
    assert farm.close_paddock("east", "south") == 0
    farm.undo()
    assert farm.get_paddocks() == ["north", "south", "east"]
    assert farm.get_count("south", "sheep") == 5
    farm.undo()
    assert farm.get_count("south", "sheep") == 4


# --- what is and is not recorded --------------------------------------------


def test_each_undo_goes_one_call_further_back():
    f = Farm()
    calls = [
        lambda: f.add_paddock("north"),
        lambda: f.add_paddock("south"),
        lambda: f.arrive("north", "cow", 5),
        lambda: f.arrive("north", "goat", 2),
        lambda: f.add_paddock("east"),
        lambda: f.arrive("south", "sheep", 4),
        lambda: f.depart("north", "cow", 1),
        lambda: f.move("cow", "north", "south", 2),
        lambda: f.move_all("south", "east"),
        lambda: f.close_paddock("north", "east"),
        lambda: f.add_paddock("west"),
        lambda: f.arrive("west", "pig", 1),
        lambda: f.move_all("south", "west"),
        lambda: f.close_paddock("west", "south"),
    ]
    states = [state(f)]
    for call in calls:
        call()
        states.append(state(f))
    assert f.get_paddocks() == ["south", "east"]
    assert f.get_count("east", "cow") == 4
    assert f.get_count("south", "pig") == 1
    for expected in reversed(states[:-1]):
        f.undo()
        assert state(f) == expected
    with pytest.raises(FarmError):
        f.undo()
    assert f.get_paddocks() == []


def test_failed_calls_are_not_recorded(farm):
    farm.arrive("east", "pig", 2)
    for call in (
        lambda: farm.depart("north", "cow", 99),
        lambda: farm.move("cow", "north", "north", 1),
        lambda: farm.move("pig", "north", "south", 1),
        lambda: farm.move_all("north", "west"),
        lambda: farm.close_paddock("north", "north"),
        lambda: farm.add_paddock("north"),
        lambda: farm.arrive("west", "cow", 1),
        lambda: farm.arrive("north", "cow", 0),
    ):
        with pytest.raises((ValueError, KeyError, FarmError)):
            call()
    farm.undo()  # the arrival of the pigs
    assert farm.get_species("east") == []
    assert farm.get_count("north", "cow") == 3


def test_get_calls_are_not_recorded(farm):
    farm.arrive("east", "pig", 2)
    farm.get_count("east", "pig")
    farm.get_species("east")
    farm.get_paddocks()
    farm.undo()
    assert farm.get_species("east") == []
    assert farm.get_count("south", "sheep") == 4


def test_there_is_no_redo():
    f = Farm()
    f.add_paddock("north")
    f.arrive("north", "cow", 3)
    f.undo()
    f.undo()
    assert f.get_paddocks() == []
    with pytest.raises(FarmError):
        f.undo()


def test_new_calls_after_an_undo_are_undone_first(farm):
    farm.arrive("east", "pig", 2)
    farm.undo()
    farm.arrive("east", "llama", 1)
    farm.undo()
    assert farm.get_species("east") == []
    farm.undo()  # the arrival of the sheep in the fixture
    assert farm.get_species("south") == []
    assert farm.get_species("north") == ["cow", "goat"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    f = Farm()
    with pytest.raises(FarmError):
        f.undo()
    f.add_paddock("north")
    f.undo()
    with pytest.raises(FarmError):
        f.undo()
    assert f.get_paddocks() == []
    f.add_paddock("north")
    f.arrive("north", "cow", 1)
    assert f.get_count("north", "cow") == 1


def test_the_whole_fixture_can_be_undone(farm):
    for _ in range(6):
        farm.undo()
    assert farm.get_paddocks() == []
    with pytest.raises(FarmError):
        farm.undo()


def test_undo_restores_counts_that_a_later_call_checks(farm):
    farm.depart("north", "cow", 3)
    farm.undo()
    farm.move("cow", "north", "south", 3)
    assert farm.get_count("south", "cow") == 3
    with pytest.raises(NotEnoughAnimals):
        farm.depart("north", "cow", 1)
