"""Hidden tests for the c_transfer change (several moves in one call). Never
shown to the writer or the editor.

Usage (with cellar.py importable, e.g. in the sandbox):
    python -m pytest changes/c_transfer/private/test_transfer_new.py
"""

import pytest
from cellar import Cellar, NotEnoughBottles


@pytest.fixture
def cellar():
    c = Cellar()
    for name in ["north", "south", "east"]:
        c.add_rack(name)
    c.store("north", 2009, 3)
    c.store("north", 2015, 4)
    c.store("south", 2015, 2)
    return c


def state(c):
    return [(r, [(v, c.get_count(r, v)) for v in held(c, r)]) for r in c.get_racks()]


def held(c, rack):
    """The rack's vintages that still have bottles (whether get_vintages also
    lists the others is unspecified)."""
    return [v for v in c.get_vintages(rack) if c.get_count(rack, v) > 0]


# --- successful transfers -----------------------------------------------------


def test_a_single_move(cellar):
    assert cellar.transfer([("north", "east", 2009, 2)]) == 2
    assert cellar.get_count("north", 2009) == 1
    assert cellar.get_count("east", 2009) == 2


def test_moves_between_several_racks(cellar):
    moves = [
        ("north", "south", 2015, 1),
        ("south", "east", 2015, 3),
        ("north", "east", 2009, 3),
    ]
    assert cellar.transfer(moves) == 7
    assert state(cellar) == [
        ("north", [(2015, 3)]),
        ("south", []),
        ("east", [(2009, 3), (2015, 3)]),
    ]


def test_a_move_can_pass_on_bottles_an_earlier_move_brought(cellar):
    moves = [("north", "east", 2009, 3), ("east", "south", 2009, 3)]
    assert cellar.transfer(moves) == 6
    assert held(cellar, "east") == []
    assert cellar.get_count("south", 2009) == 3
    assert held(cellar, "north") == [2015]


def test_two_moves_may_take_from_the_same_rack(cellar):
    moves = [("north", "south", 2015, 2), ("north", "east", 2015, 2)]
    assert cellar.transfer(moves) == 4
    assert held(cellar, "north") == [2009]
    assert cellar.get_count("south", 2015) == 4
    assert cellar.get_count("east", 2015) == 2


def test_moves_that_return_bottles_leave_the_counts_as_they_were(cellar):
    before = state(cellar)
    moves = [("south", "east", 2015, 2), ("east", "south", 2015, 2)]
    assert cellar.transfer(moves) == 4
    assert state(cellar) == before


def test_moved_bottles_are_ordinary_bottles(cellar):
    cellar.transfer([("north", "east", 2015, 4)])
    cellar.take("east", 2015, 1)
    assert cellar.relocate_all("east", "south") == 3
    assert cellar.decommission_rack("north", "south") == 3
    assert cellar.get_count("south", 2015) == 5
    assert cellar.get_count("south", 2009) == 3


# --- failed transfers change nothing ----------------------------------------


def test_too_many_bottles_in_the_last_move_cancels_every_move(cellar):
    before = state(cellar)
    moves = [
        ("north", "east", 2009, 3),
        ("north", "east", 2015, 4),
        ("south", "east", 2015, 3),
    ]
    with pytest.raises(NotEnoughBottles):
        cellar.transfer(moves)
    assert state(cellar) == before


def test_two_moves_from_the_same_rack_need_enough_for_both(cellar):
    before = state(cellar)
    moves = [("north", "south", 2015, 3), ("north", "east", 2015, 3)]
    with pytest.raises(NotEnoughBottles):
        cellar.transfer(moves)
    assert state(cellar) == before


def test_a_vintage_the_rack_does_not_have_cancels_every_move(cellar):
    before = state(cellar)
    with pytest.raises(NotEnoughBottles):
        cellar.transfer([("north", "east", 2015, 1), ("south", "east", 2009, 1)])
    assert state(cellar) == before


def test_bottles_moved_away_earlier_in_the_call_are_no_longer_there(cellar):
    before = state(cellar)
    moves = [("south", "east", 2015, 2), ("south", "north", 2015, 1)]
    with pytest.raises(NotEnoughBottles):
        cellar.transfer(moves)
    assert state(cellar) == before


@pytest.mark.parametrize(
    "bad_move",
    [
        ("west", "east", 2015, 1),
        ("north", "west", 2015, 1),
    ],
    ids=["from", "to"],
)
def test_a_rack_not_in_use_cancels_every_move(cellar, bad_move):
    before = state(cellar)
    with pytest.raises(KeyError):
        cellar.transfer([("north", "east", 2015, 2), bad_move])
    assert state(cellar) == before


@pytest.mark.parametrize(
    "bad_move",
    [
        ("north", "east", 2009, 0),
        ("north", "east", 2009, -1),
        ("north", "north", 2009, 1),
    ],
    ids=["zero", "negative", "same_rack"],
)
def test_a_bad_count_or_the_same_rack_cancels_every_move(cellar, bad_move):
    before = state(cellar)
    with pytest.raises(ValueError):
        cellar.transfer([("north", "east", 2015, 2), bad_move])
    assert state(cellar) == before


def test_a_decommissioned_rack_cannot_be_used(cellar):
    cellar.decommission_rack("east", "south")
    before = state(cellar)
    with pytest.raises(KeyError):
        cellar.transfer([("north", "east", 2015, 1)])
    assert state(cellar) == before


def test_a_cancelled_transfer_can_be_retried_without_the_bad_move(cellar):
    with pytest.raises(NotEnoughBottles):
        cellar.transfer([("north", "east", 2015, 4), ("north", "east", 2009, 4)])
    assert cellar.transfer([("north", "east", 2015, 4), ("north", "east", 2009, 3)]) == 7
    assert held(cellar, "north") == []
    assert held(cellar, "east") == [2009, 2015]
