"""Hidden tests for the initial aquarium_tanks spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with aquarium.py importable, e.g. in the sandbox):
    python -m pytest private/test_aquarium_initial.py
"""

import pytest
from aquarium import Aquarium, AquariumError, NotEnoughFish

BAD_COUNTS = [0, -3]


@pytest.fixture
def aquarium():
    a = Aquarium()
    for name in ["reef", "lagoon", "kelp"]:
        a.add_tank(name)
    a.add_fish("reef", "tang", 5)
    a.add_fish("reef", "clownfish", 2)
    return a


def state(a):
    """Every tank in order with its species and counts, to check that a
    failed call changed nothing."""
    return [(t, [(s, a.get_count(t, s)) for s in a.get_species(t)]) for t in a.get_tanks()]


# --- tanks ------------------------------------------------------------------


def test_a_new_tank_is_empty():
    a = Aquarium()
    a.add_tank("reef")
    assert a.get_species("reef") == []
    assert a.get_count("reef", "tang") == 0


def test_tanks_keep_the_order_they_were_added_in():
    a = Aquarium()
    for name in ["lagoon", "reef", "kelp", "arctic"]:
        a.add_tank(name)
    assert a.get_tanks() == ["lagoon", "reef", "kelp", "arctic"]


def test_a_name_in_use_cannot_be_added_again(aquarium):
    before = state(aquarium)
    with pytest.raises(AquariumError):
        aquarium.add_tank("reef")
    assert state(aquarium) == before


def test_a_drained_name_can_be_added_again_as_a_new_empty_tank(aquarium):
    aquarium.drain_tank("reef", "kelp")
    aquarium.add_tank("reef")
    assert aquarium.get_tanks() == ["lagoon", "kelp", "reef"]
    assert aquarium.get_species("reef") == []
    assert aquarium.get_count("kelp", "tang") == 5


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.add_fish("arctic", "tang", 1),
        lambda a: a.remove_fish("arctic", "tang", 1),
        lambda a: a.move_all("arctic", "lagoon"),
        lambda a: a.move_all("reef", "arctic"),
        lambda a: a.drain_tank("arctic", "lagoon"),
        lambda a: a.drain_tank("reef", "arctic"),
        lambda a: a.get_count("arctic", "tang"),
        lambda a: a.get_species("arctic"),
    ],
)
def test_tanks_never_added_raise_key_error(aquarium, call):
    before = state(aquarium)
    with pytest.raises(KeyError):
        call(aquarium)
    assert state(aquarium) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.add_fish("kelp", "tang", 1),
        lambda a: a.move_all("kelp", "reef"),
        lambda a: a.move_all("reef", "kelp"),
        lambda a: a.drain_tank("kelp", "reef"),
        lambda a: a.drain_tank("reef", "kelp"),
        lambda a: a.get_count("kelp", "tang"),
        lambda a: a.get_species("kelp"),
    ],
)
def test_a_drained_tank_is_not_in_use(aquarium, call):
    aquarium.drain_tank("kelp", "lagoon")  # kelp is empty
    before = state(aquarium)
    with pytest.raises(KeyError):
        call(aquarium)
    assert state(aquarium) == before


# --- putting fish in and taking them out --------------------------------------


def test_fish_put_in_and_taken_out_change_the_counts(aquarium):
    aquarium.add_fish("reef", "tang", 3)
    aquarium.remove_fish("reef", "tang", 6)
    aquarium.add_fish("lagoon", "tang", 1)
    assert aquarium.get_count("reef", "tang") == 2
    assert aquarium.get_count("lagoon", "tang") == 1
    assert aquarium.get_count("reef", "clownfish") == 2


def test_every_fish_of_a_species_can_be_taken_out(aquarium):
    aquarium.remove_fish("reef", "tang", 5)
    assert aquarium.get_count("reef", "tang") == 0
    assert aquarium.get_species("reef") == ["clownfish"]


def test_taking_out_too_many_fish_raises_and_changes_nothing(aquarium):
    before = state(aquarium)
    with pytest.raises(NotEnoughFish):
        aquarium.remove_fish("reef", "clownfish", 3)
    with pytest.raises(NotEnoughFish):
        aquarium.remove_fish("reef", "guppy", 1)
    with pytest.raises(NotEnoughFish):
        aquarium.remove_fish("lagoon", "tang", 1)
    assert state(aquarium) == before


def test_species_are_listed_in_alphabetical_order():
    a = Aquarium()
    a.add_tank("reef")
    a.add_fish("reef", "tang", 1)
    a.add_fish("reef", "angelfish", 2)
    a.add_fish("reef", "clownfish", 3)
    assert a.get_species("reef") == ["angelfish", "clownfish", "tang"]


@pytest.mark.parametrize("count", BAD_COUNTS)
def test_add_fish_rejects_counts_of_0_or_less(aquarium, count):
    before = state(aquarium)
    with pytest.raises(ValueError):
        aquarium.add_fish("reef", "tang", count)
    assert state(aquarium) == before


# --- moving -----------------------------------------------------------------


def test_move_all_moves_every_species_next_to_the_fish_already_there(aquarium):
    aquarium.add_fish("lagoon", "angelfish", 4)
    assert aquarium.move_all("reef", "lagoon") == 7
    assert aquarium.get_species("reef") == []
    assert aquarium.get_species("lagoon") == ["angelfish", "clownfish", "tang"]
    assert aquarium.get_count("lagoon", "tang") == 5
    assert aquarium.get_count("lagoon", "clownfish") == 2
    assert aquarium.get_count("lagoon", "angelfish") == 4
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]


def test_a_tank_emptied_by_move_all_can_take_fish_again(aquarium):
    aquarium.move_all("reef", "kelp")
    aquarium.add_fish("reef", "guppy", 3)
    assert aquarium.get_species("reef") == ["guppy"]
    assert aquarium.get_count("kelp", "tang") == 5


def test_move_all_from_an_empty_tank_moves_nothing(aquarium):
    before = state(aquarium)
    assert aquarium.move_all("kelp", "reef") == 0
    assert state(aquarium) == before


def test_drain_tank_moves_every_fish_and_removes_the_tank(aquarium):
    aquarium.add_fish("kelp", "seahorse", 2)
    assert aquarium.drain_tank("reef", "kelp") == 7
    assert aquarium.get_tanks() == ["lagoon", "kelp"]
    assert aquarium.get_count("kelp", "tang") == 5
    assert aquarium.get_count("kelp", "seahorse") == 2
    assert aquarium.get_count("kelp", "clownfish") == 2


def test_draining_an_empty_tank_removes_it(aquarium):
    assert aquarium.drain_tank("lagoon", "reef") == 0
    assert aquarium.get_tanks() == ["reef", "kelp"]
    assert aquarium.get_count("reef", "tang") == 5


def test_the_other_tanks_keep_their_order_after_a_drain(aquarium):
    aquarium.add_tank("arctic")
    aquarium.drain_tank("lagoon", "arctic")
    assert aquarium.get_tanks() == ["reef", "kelp", "arctic"]


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.move_all("reef", "reef"),
        lambda a: a.drain_tank("reef", "reef"),
    ],
    ids=["move_all", "drain_tank"],
)
def test_the_same_tank_on_both_sides_is_rejected(aquarium, call):
    before = state(aquarium)
    with pytest.raises(ValueError):
        call(aquarium)
    assert state(aquarium) == before


# --- general ----------------------------------------------------------------


def test_not_enough_fish_is_an_aquarium_error():
    assert issubclass(NotEnoughFish, AquariumError)


def test_aquariums_do_not_share_tanks():
    first, second = Aquarium(), Aquarium()
    first.add_tank("reef")
    first.add_fish("reef", "tang", 3)
    assert second.get_tanks() == []
    second.add_tank("reef")
    assert second.get_count("reef", "tang") == 0
