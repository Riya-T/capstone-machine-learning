"""Hidden tests for the transfer change. Never shown to the writer or the
editor.

Usage (with aquarium.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/private/test_transfer_new.py
"""

import pytest
from aquarium import Aquarium, NotEnoughFish


@pytest.fixture
def aquarium():
    a = Aquarium()
    for name in ["reef", "lagoon", "kelp"]:
        a.add_tank(name)
    a.add_fish("reef", "tang", 4)
    a.add_fish("reef", "clownfish", 2)
    a.add_fish("lagoon", "guppy", 3)
    return a


def state(a):
    return [(t, [(s, a.get_count(t, s)) for s in a.get_species(t)]) for t in a.get_tanks()]


# --- successful transfers ---------------------------------------------------------


def test_a_transfer_of_one_move(aquarium):
    assert aquarium.transfer([("tang", "reef", "kelp", 3)]) == 3
    assert aquarium.get_count("reef", "tang") == 1
    assert aquarium.get_count("kelp", "tang") == 3


def test_a_transfer_of_several_moves_returns_the_total(aquarium):
    moves = [
        ("tang", "reef", "kelp", 2),
        ("guppy", "lagoon", "reef", 1),
        ("clownfish", "reef", "lagoon", 2),
    ]
    assert aquarium.transfer(moves) == 5
    assert state(aquarium) == [
        ("reef", [("guppy", 1), ("tang", 2)]),
        ("lagoon", [("clownfish", 2), ("guppy", 2)]),
        ("kelp", [("tang", 2)]),
    ]


def test_a_move_may_use_fish_an_earlier_move_brought_in(aquarium):
    moves = [("tang", "reef", "kelp", 4), ("tang", "kelp", "lagoon", 3)]
    assert aquarium.transfer(moves) == 7
    assert aquarium.get_count("kelp", "tang") == 1
    assert aquarium.get_count("lagoon", "tang") == 3
    assert aquarium.get_species("reef") == ["clownfish"]


def test_two_moves_of_the_same_species_from_the_same_tank_add_up(aquarium):
    assert aquarium.transfer([("tang", "reef", "kelp", 1), ("tang", "reef", "lagoon", 3)]) == 4
    assert aquarium.get_species("reef") == ["clownfish"]
    assert aquarium.get_count("kelp", "tang") == 1
    assert aquarium.get_count("lagoon", "tang") == 3


def test_a_transfer_keeps_the_list_of_tanks(aquarium):
    aquarium.transfer([("guppy", "lagoon", "kelp", 3)])
    assert aquarium.get_tanks() == ["reef", "lagoon", "kelp"]
    assert aquarium.get_species("lagoon") == []


def test_fish_moved_by_a_transfer_can_be_moved_again(aquarium):
    aquarium.transfer([("guppy", "lagoon", "kelp", 2)])
    assert aquarium.move_all("kelp", "reef") == 2
    aquarium.remove_fish("reef", "guppy", 2)
    assert aquarium.get_species("reef") == ["clownfish", "tang"]


# --- failed transfers change nothing ----------------------------------------------


def test_a_later_move_cannot_use_fish_an_earlier_move_took_away(aquarium):
    before = state(aquarium)
    with pytest.raises(NotEnoughFish):
        aquarium.transfer([("tang", "reef", "kelp", 3), ("tang", "reef", "lagoon", 2)])
    assert state(aquarium) == before


def test_a_move_of_a_species_the_tank_lacks_fails_the_whole_transfer(aquarium):
    before = state(aquarium)
    with pytest.raises(NotEnoughFish):
        aquarium.transfer([("tang", "reef", "kelp", 1), ("seahorse", "lagoon", "kelp", 1)])
    assert state(aquarium) == before


def test_a_failing_first_move_changes_nothing(aquarium):
    before = state(aquarium)
    with pytest.raises(NotEnoughFish):
        aquarium.transfer([("guppy", "lagoon", "kelp", 4), ("tang", "reef", "kelp", 1)])
    assert state(aquarium) == before


@pytest.mark.parametrize(
    "bad_move",
    [
        ("tang", "arctic", "kelp", 1),
        ("tang", "kelp", "arctic", 1),
    ],
    ids=["from_unknown", "to_unknown"],
)
def test_a_tank_not_in_use_fails_the_whole_transfer(aquarium, bad_move):
    before = state(aquarium)
    with pytest.raises(KeyError):
        aquarium.transfer([("tang", "reef", "kelp", 2), bad_move])
    assert state(aquarium) == before


def test_a_drained_tank_fails_the_whole_transfer(aquarium):
    aquarium.drain_tank("kelp", "lagoon")
    before = state(aquarium)
    with pytest.raises(KeyError):
        aquarium.transfer([("guppy", "lagoon", "reef", 1), ("tang", "reef", "kelp", 1)])
    assert state(aquarium) == before


@pytest.mark.parametrize(
    "bad_move",
    [
        ("tang", "kelp", "reef", 0),
        ("tang", "kelp", "reef", -2),
        ("tang", "kelp", "kelp", 1),
    ],
    ids=["count_0", "count_negative", "same_tank"],
)
def test_a_move_with_a_bad_value_fails_the_whole_transfer(aquarium, bad_move):
    before = state(aquarium)
    with pytest.raises(ValueError):
        aquarium.transfer([("tang", "reef", "kelp", 2), bad_move])
    assert state(aquarium) == before


def test_a_failed_transfer_can_be_followed_by_a_good_one(aquarium):
    with pytest.raises(NotEnoughFish):
        aquarium.transfer([("tang", "reef", "kelp", 4), ("tang", "kelp", "lagoon", 5)])
    assert aquarium.transfer([("tang", "reef", "kelp", 4), ("tang", "kelp", "lagoon", 4)]) == 8
    assert aquarium.get_species("kelp") == []
    assert aquarium.get_count("lagoon", "tang") == 4
