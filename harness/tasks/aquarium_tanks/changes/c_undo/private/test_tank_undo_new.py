"""Hidden tests for the undo change. Never shown to the writer or the
editor.

Usage (with aquarium.py importable, e.g. in the sandbox):
    python -m pytest changes/c_undo/private/test_tank_undo_new.py
"""

import pytest
from aquarium import Aquarium, AquariumError, NotEnoughFish


@pytest.fixture
def aquarium():
    a = Aquarium()
    for name in ["reef", "lagoon", "kelp"]:
        a.add_tank(name)
    a.add_fish("reef", "tang", 3)
    a.add_fish("reef", "clownfish", 2)
    a.add_fish("lagoon", "guppy", 4)
    return a


def state(a):
    return [(t, [(s, a.get_count(t, s)) for s in a.get_species(t)]) for t in a.get_tanks()]


# --- simple calls -------------------------------------------------------------


def test_undo_of_fish_of_a_new_species(aquarium):
    before = state(aquarium)
    aquarium.add_fish("kelp", "seahorse", 2)
    aquarium.undo()
    assert state(aquarium) == before
    assert aquarium.get_species("kelp") == []


def test_undo_of_more_fish_of_a_species(aquarium):
    aquarium.add_fish("reef", "tang", 5)
    aquarium.undo()
    assert aquarium.get_count("reef", "tang") == 3


def test_undo_of_taking_out_some_fish(aquarium):
    before = state(aquarium)
    aquarium.remove_fish("reef", "tang", 1)
    aquarium.undo()
    assert state(aquarium) == before


def test_undo_of_taking_out_every_fish_of_a_species(aquarium):
    aquarium.remove_fish("reef", "clownfish", 2)
    aquarium.undo()
    assert aquarium.get_species("reef") == ["clownfish", "tang"]
    assert aquarium.get_count("reef", "clownfish") == 2


# --- composite calls are undone as a whole ------------------------------------


def test_one_undo_takes_back_a_whole_move_all(aquarium):
    before = state(aquarium)
    assert aquarium.move_all("reef", "kelp") == 5
    aquarium.undo()
    assert state(aquarium) == before
    assert aquarium.get_species("kelp") == []


def test_undo_of_a_move_all_into_a_tank_with_other_fish(aquarium):
    before = state(aquarium)
    assert aquarium.move_all("reef", "lagoon") == 5
    assert aquarium.get_species("lagoon") == ["clownfish", "guppy", "tang"]
    aquarium.undo()
    assert state(aquarium) == before
    assert aquarium.get_species("lagoon") == ["guppy"]


def test_undo_of_drain_tank_brings_it_back_with_its_fish(aquarium):
    before = state(aquarium)
    assert aquarium.drain_tank("reef", "kelp") == 5
    aquarium.undo()
    assert state(aquarium) == before
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]
    assert aquarium.get_count("kelp", "tang") == 0


def test_a_tank_brought_back_keeps_its_place_in_the_list(aquarium):
    aquarium.add_tank("arctic")
    before = state(aquarium)
    aquarium.drain_tank("lagoon", "arctic")
    assert aquarium.get_tanks() == ["reef", "kelp", "arctic"]
    aquarium.undo()
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp", "arctic"]
    assert state(aquarium) == before


def test_a_tank_brought_back_is_in_use_again(aquarium):
    aquarium.drain_tank("reef", "kelp")
    aquarium.undo()
    aquarium.add_fish("reef", "tang", 1)
    assert aquarium.get_count("reef", "tang") == 4
    with pytest.raises(AquariumError):
        aquarium.add_tank("reef")
    assert aquarium.drain_tank("reef", "lagoon") == 6
    assert aquarium.get_tanks() == ["lagoon", "kelp"]


def test_undo_of_draining_an_empty_tank_brings_it_back(aquarium):
    assert aquarium.drain_tank("kelp", "lagoon") == 0
    aquarium.undo()
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]
    assert aquarium.get_species("kelp") == []
    aquarium.add_fish("kelp", "seahorse", 1)
    assert aquarium.get_count("kelp", "seahorse") == 1


def test_undo_of_add_tank_removes_it_and_frees_the_name(aquarium):
    aquarium.add_tank("arctic")
    aquarium.undo()
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]
    with pytest.raises(KeyError):
        aquarium.get_species("arctic")
    aquarium.add_tank("arctic")
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp", "arctic"]
    assert aquarium.get_species("arctic") == []


def test_undo_through_a_name_that_was_drained_and_added_again(aquarium):
    aquarium.add_tank("arctic")
    aquarium.add_fish("arctic", "cod", 2)
    aquarium.drain_tank("arctic", "kelp")
    aquarium.add_tank("arctic")  # a new, empty arctic
    aquarium.add_fish("arctic", "char", 1)
    aquarium.undo()  # the char
    aquarium.undo()  # the new arctic
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]
    aquarium.undo()  # the drain: the old arctic comes back with its cod
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp", "arctic"]
    assert aquarium.get_species("arctic") == ["cod"]
    assert aquarium.get_count("kelp", "cod") == 0
    aquarium.undo()  # the cod
    aquarium.undo()  # the first arctic
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]


# --- what is and is not recorded ----------------------------------------------


def test_each_undo_goes_one_call_further_back():
    a = Aquarium()
    calls = [
        lambda: a.add_tank("reef"),
        lambda: a.add_tank("lagoon"),
        lambda: a.add_fish("reef", "tang", 5),
        lambda: a.add_fish("reef", "clownfish", 2),
        lambda: a.add_tank("kelp"),
        lambda: a.add_fish("lagoon", "guppy", 4),
        lambda: a.remove_fish("reef", "tang", 1),
        lambda: a.move_all("lagoon", "kelp"),
        lambda: a.drain_tank("reef", "kelp"),
        lambda: a.add_tank("arctic"),
        lambda: a.add_fish("arctic", "cod", 1),
        lambda: a.move_all("kelp", "lagoon"),
        lambda: a.drain_tank("arctic", "lagoon"),
    ]
    states = [state(a)]
    for call in calls:
        call()
        states.append(state(a))
    assert a.get_tanks() == ["lagoon", "kelp"]
    assert a.get_count("lagoon", "tang") == 4
    assert a.get_count("lagoon", "cod") == 1
    for expected in reversed(states[:-1]):
        a.undo()
        assert state(a) == expected
    with pytest.raises(AquariumError):
        a.undo()
    assert a.get_tanks() == []


def test_failed_calls_are_not_recorded(aquarium):
    aquarium.add_fish("kelp", "seahorse", 2)
    for call in (
        lambda: aquarium.remove_fish("reef", "tang", 99),
        lambda: aquarium.remove_fish("kelp", "cod", 1),
        lambda: aquarium.move_all("reef", "reef"),
        lambda: aquarium.move_all("reef", "arctic"),
        lambda: aquarium.drain_tank("reef", "reef"),
        lambda: aquarium.drain_tank("arctic", "reef"),
        lambda: aquarium.add_tank("reef"),
        lambda: aquarium.add_fish("arctic", "tang", 1),
        lambda: aquarium.add_fish("reef", "tang", 0),
    ):
        with pytest.raises((ValueError, KeyError, AquariumError)):
            call()
    aquarium.undo()  # the seahorses
    assert aquarium.get_species("kelp") == []
    assert aquarium.get_count("reef", "tang") == 3
    aquarium.undo()  # the guppies
    assert aquarium.get_species("lagoon") == []


def test_get_calls_are_not_recorded(aquarium):
    aquarium.add_fish("kelp", "seahorse", 2)
    aquarium.get_count("kelp", "seahorse")
    aquarium.get_species("kelp")
    aquarium.get_tanks()
    aquarium.undo()
    assert aquarium.get_species("kelp") == []
    assert aquarium.get_count("lagoon", "guppy") == 4


def test_there_is_no_redo():
    a = Aquarium()
    a.add_tank("reef")
    a.add_fish("reef", "tang", 3)
    a.undo()
    a.undo()
    assert a.get_tanks() == []
    with pytest.raises(AquariumError):
        a.undo()


def test_a_new_call_after_an_undo_is_undone_first(aquarium):
    aquarium.add_fish("kelp", "seahorse", 2)
    aquarium.undo()
    aquarium.add_fish("kelp", "cod", 1)
    aquarium.undo()
    assert aquarium.get_species("kelp") == []
    aquarium.undo()  # the guppies from the fixture
    assert aquarium.get_species("lagoon") == []
    assert aquarium.get_species("reef") == ["clownfish", "tang"]


def test_nothing_left_to_undo_raises_and_changes_nothing():
    a = Aquarium()
    with pytest.raises(AquariumError):
        a.undo()
    a.add_tank("reef")
    a.undo()
    with pytest.raises(AquariumError):
        a.undo()
    assert a.get_tanks() == []
    a.add_tank("reef")
    a.add_fish("reef", "tang", 1)
    assert a.get_count("reef", "tang") == 1


def test_the_whole_fixture_can_be_undone(aquarium):
    for _ in range(6):
        aquarium.undo()
    assert aquarium.get_tanks() == []
    with pytest.raises(AquariumError):
        aquarium.undo()


def test_counts_put_back_by_undo_are_used_by_later_calls(aquarium):
    aquarium.remove_fish("reef", "tang", 3)
    aquarium.undo()
    assert aquarium.move_all("reef", "lagoon") == 5
    assert aquarium.get_count("lagoon", "tang") == 3
    with pytest.raises(NotEnoughFish):
        aquarium.remove_fish("reef", "tang", 1)
