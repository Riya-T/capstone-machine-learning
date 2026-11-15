"""Hidden tests for the c_quarantine change (quarantined paddocks). Never
shown to the writer or the editor. c_quarantine only comes after c_allowed,
so these tests also check that allowed species still work.

Usage (with farm.py importable, e.g. in the sandbox):
    python -m pytest changes/c_quarantine/private/test_quarantine_new.py
"""

import pytest
from farm import Farm, FarmError, NotAllowed, NotEnoughAnimals, Quarantined


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


# --- every call that moves animals --------------------------------------------


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.arrive("north", "cow", 1),
        lambda f: f.depart("north", "cow", 1),
        lambda f: f.move("cow", "north", "south", 1),
        lambda f: f.move("sheep", "south", "north", 1),
        lambda f: f.move_all("north", "south"),
        lambda f: f.move_all("south", "north"),
        lambda f: f.close_paddock("north", "south"),
        lambda f: f.close_paddock("south", "north"),
    ],
    ids=[
        "arrive",
        "depart",
        "move_out",
        "move_in",
        "move_all_out",
        "move_all_in",
        "close_quarantined",
        "close_into_quarantined",
    ],
)
def test_a_quarantined_paddock_refuses_every_movement(farm, call):
    farm.quarantine("north")
    before = state(farm)
    with pytest.raises(Quarantined):
        call(farm)
    assert state(farm) == before
    assert farm.get_paddocks() == ["north", "south", "east"]


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.move_all("east", "south"),
        lambda f: f.move_all("south", "east"),
        lambda f: f.close_paddock("east", "south"),
        lambda f: f.close_paddock("south", "east"),
    ],
    ids=["move_all_out", "move_all_in", "close_quarantined", "close_into_quarantined"],
)
def test_quarantine_refuses_even_when_nothing_would_move(farm, call):
    # east and south are both empty, so none of these calls would move an animal.
    farm.depart("south", "sheep", 4)
    farm.quarantine("east")
    before = state(farm)
    with pytest.raises(Quarantined):
        call(farm)
    assert state(farm) == before


def test_other_paddocks_are_not_affected(farm):
    farm.quarantine("north")
    farm.arrive("east", "pig", 2)
    farm.move("sheep", "south", "east", 1)
    assert farm.move_all("east", "south") == 3
    assert farm.close_paddock("east", "south") == 0
    assert farm.get_count("south", "pig") == 2
    assert farm.get_count("north", "cow") == 3


def test_release_lifts_the_quarantine(farm):
    farm.quarantine("north")
    farm.release("north")
    farm.arrive("north", "cow", 1)
    farm.depart("north", "goat", 1)
    farm.move("cow", "north", "south", 2)
    assert farm.move_all("south", "north") == 6
    assert farm.close_paddock("north", "east") == 9
    assert farm.get_count("east", "cow") == 4


def test_quarantining_twice_then_releasing_once_lifts_it(farm):
    farm.quarantine("north")
    farm.quarantine("north")
    farm.release("north")
    farm.arrive("north", "cow", 1)
    assert farm.get_count("north", "cow") == 4


def test_releasing_a_paddock_that_is_not_quarantined_does_nothing(farm):
    farm.release("north")
    farm.arrive("north", "cow", 1)
    farm.quarantine("north")
    farm.release("south")
    with pytest.raises(Quarantined):
        farm.arrive("north", "cow", 1)
    assert farm.get_count("north", "cow") == 4


@pytest.mark.parametrize(
    "call",
    [
        lambda f: f.quarantine("west"),
        lambda f: f.release("west"),
        lambda f: f.quarantine("east"),  # closed below
        lambda f: f.release("east"),
    ],
)
def test_paddocks_not_in_use_raise_key_error_for_quarantine(farm, call):
    farm.close_paddock("east", "south")
    with pytest.raises(KeyError):
        call(farm)


def test_calls_that_move_no_animals_still_work(farm):
    farm.quarantine("north")
    assert farm.get_count("north", "cow") == 3
    assert farm.get_species("north") == ["cow", "goat"]
    assert farm.get_paddocks() == ["north", "south", "east"]
    farm.set_allowed("north", ["cow"])
    assert farm.get_allowed("north") == ["cow"]
    farm.add_paddock("west")
    assert farm.get_paddocks() == ["north", "south", "east", "west"]


def test_quarantined_is_a_farm_error_of_its_own():
    assert issubclass(Quarantined, FarmError)
    assert not issubclass(Quarantined, NotEnoughAnimals)
    assert not issubclass(Quarantined, NotAllowed)


# --- order of errors ----------------------------------------------------------


def test_a_paddock_not_in_use_is_reported_before_quarantined(farm):
    farm.quarantine("north")
    with pytest.raises(KeyError):
        farm.move("cow", "north", "west", 1)
    with pytest.raises(KeyError):
        farm.move_all("west", "north")
    with pytest.raises(KeyError):
        farm.close_paddock("north", "west")


def test_a_bad_count_or_same_paddock_is_reported_before_quarantined(farm):
    farm.quarantine("north")
    before = state(farm)
    with pytest.raises(ValueError):
        farm.arrive("north", "cow", 0)
    with pytest.raises(ValueError):
        farm.depart("north", "cow", -1)
    with pytest.raises(ValueError):
        farm.move("cow", "south", "north", 0)
    with pytest.raises(ValueError):
        farm.move("cow", "north", "north", 1)
    with pytest.raises(ValueError):
        farm.move_all("north", "north")
    with pytest.raises(ValueError):
        farm.close_paddock("north", "north")
    assert state(farm) == before


def test_quarantined_is_reported_before_not_enough_animals(farm):
    farm.quarantine("north")
    with pytest.raises(Quarantined):
        farm.depart("north", "cow", 99)
    with pytest.raises(Quarantined):
        farm.move("llama", "north", "south", 1)
    with pytest.raises(Quarantined):
        farm.move("cow", "south", "north", 1)


def test_quarantined_is_reported_before_not_allowed(farm):
    farm.set_allowed("east", [])
    farm.quarantine("east")
    before = state(farm)
    with pytest.raises(Quarantined):
        farm.arrive("east", "cow", 1)
    with pytest.raises(Quarantined):
        farm.move("cow", "north", "east", 1)
    with pytest.raises(Quarantined):
        farm.move_all("north", "east")
    with pytest.raises(Quarantined):
        farm.close_paddock("north", "east")
    assert state(farm) == before


# --- allowed species still work for every call --------------------------------


def test_allowed_species_still_limit_every_call_that_brings_animals_in(farm):
    # south holds only sheep, so each call below would bring in one species.
    farm.set_allowed("east", ["cow"])
    before = state(farm)
    with pytest.raises(NotAllowed):
        farm.arrive("east", "sheep", 1)
    with pytest.raises(NotAllowed):
        farm.move("sheep", "south", "east", 1)
    with pytest.raises(NotAllowed):
        farm.move_all("south", "east")
    with pytest.raises(NotAllowed):
        farm.close_paddock("south", "east")
    assert state(farm) == before


def test_allowed_species_still_let_allowed_animals_in(farm):
    farm.set_allowed("east", ["sheep"])
    farm.arrive("east", "sheep", 1)
    farm.move("sheep", "south", "east", 1)
    assert farm.move_all("south", "east") == 3
    farm.set_allowed("south", ["cow", "goat"])
    assert farm.close_paddock("north", "south") == 5
    assert farm.get_count("east", "sheep") == 5
    assert farm.get_species("south") == ["cow", "goat"]


def test_a_released_paddock_still_checks_its_allowed_species(farm):
    farm.set_allowed("east", ["sheep"])
    farm.quarantine("east")
    farm.release("east")
    with pytest.raises(NotAllowed):
        farm.move("cow", "north", "east", 1)
    farm.move("sheep", "south", "east", 2)
    assert farm.get_count("east", "sheep") == 2
