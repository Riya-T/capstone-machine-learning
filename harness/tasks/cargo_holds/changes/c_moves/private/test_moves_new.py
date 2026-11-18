"""Hidden tests for the c_moves change (restowing plans). Never shown to the
writer or the editor. They call only the spec's methods and this change's
own, never undo.

Usage (with ship.py importable, e.g. in the sandbox):
    python -m pytest changes/c_moves/private/test_moves_new.py
"""

import pytest
from ship import NotEnoughCrates, Ship


@pytest.fixture
def ship():
    s = Ship()
    for name in ["fore", "mid", "aft"]:
        s.add_hold(name)
    s.load("fore", "grain", 5)
    s.load("fore", "steel", 2)
    s.load("mid", "coal", 4)
    return s


def state(s):
    return [(h, [(c, s.get_count(h, c)) for c in s.get_cargo(h)]) for h in s.get_holds()]


# --- plans that work --------------------------------------------------------------


def test_a_single_move(ship):
    assert ship.apply_moves([("grain", "fore", "aft", 2)]) == 2
    assert ship.get_count("fore", "grain") == 3
    assert ship.get_count("aft", "grain") == 2


def test_several_moves_return_the_total(ship):
    moves = [("grain", "fore", "mid", 1), ("coal", "mid", "aft", 3), ("steel", "fore", "aft", 1)]
    assert ship.apply_moves(moves) == 5
    assert state(ship) == [
        ("fore", [("grain", 4), ("steel", 1)]),
        ("mid", [("coal", 1), ("grain", 1)]),
        ("aft", [("coal", 3), ("steel", 1)]),
    ]


def test_moves_onto_the_same_cargo_type_add_up(ship):
    ship.load("aft", "grain", 1)
    ship.apply_moves([("grain", "fore", "aft", 2), ("grain", "fore", "aft", 3)])
    assert ship.get_count("aft", "grain") == 6
    assert ship.get_cargo("fore") == ["steel"]


def test_a_move_may_use_crates_brought_in_by_an_earlier_move(ship):
    moves = [("grain", "fore", "aft", 5), ("grain", "aft", "mid", 4)]
    assert ship.apply_moves(moves) == 9
    assert ship.get_count("aft", "grain") == 1
    assert ship.get_count("mid", "grain") == 4
    assert ship.get_cargo("fore") == ["steel"]


def test_crates_may_go_out_and_come_back(ship):
    ship.apply_moves([("steel", "fore", "mid", 2), ("steel", "mid", "fore", 1)])
    assert ship.get_count("fore", "steel") == 1
    assert ship.get_count("mid", "steel") == 1


def test_moving_every_crate_of_a_cargo_type_unlists_it(ship):
    ship.apply_moves([("coal", "mid", "fore", 4)])
    assert ship.get_cargo("mid") == []
    assert ship.get_cargo("fore") == ["coal", "grain", "steel"]


def test_apply_moves_keeps_the_holds_and_their_order(ship):
    ship.apply_moves([("grain", "fore", "aft", 5), ("steel", "fore", "aft", 2)])
    assert ship.get_holds() == ["fore", "mid", "aft"]
    assert ship.get_cargo("fore") == []
    ship.load("fore", "wool", 1)
    assert ship.get_count("fore", "wool") == 1


def test_the_plan_can_be_given_twice(ship):
    moves = [("grain", "fore", "aft", 2)]
    ship.apply_moves(moves)
    ship.apply_moves(moves)
    assert ship.get_count("aft", "grain") == 4
    assert moves == [("grain", "fore", "aft", 2)]


def test_plans_work_with_the_other_methods(ship):
    ship.apply_moves([("grain", "fore", "mid", 5)])
    assert ship.shift_all("mid", "aft") == 9
    assert ship.seal_hold("aft", "fore") == 9
    assert ship.get_holds() == ["fore", "mid"]
    assert ship.get_count("fore", "grain") == 5


# --- plans that fail change nothing -----------------------------------------------


def test_too_few_crates_in_the_first_move(ship):
    before = state(ship)
    with pytest.raises(NotEnoughCrates):
        ship.apply_moves([("grain", "fore", "aft", 6), ("steel", "fore", "aft", 1)])
    assert state(ship) == before


def test_too_few_crates_in_a_later_move_undoes_the_earlier_ones(ship):
    before = state(ship)
    with pytest.raises(NotEnoughCrates):
        ship.apply_moves(
            [("grain", "fore", "aft", 3), ("coal", "mid", "aft", 4), ("steel", "fore", "aft", 3)]
        )
    assert state(ship) == before


def test_a_cargo_type_the_hold_has_none_of(ship):
    before = state(ship)
    with pytest.raises(NotEnoughCrates):
        ship.apply_moves([("grain", "fore", "mid", 1), ("wool", "mid", "aft", 1)])
    assert state(ship) == before


def test_moves_see_the_crates_that_earlier_moves_took_away(ship):
    before = state(ship)
    with pytest.raises(NotEnoughCrates):
        ship.apply_moves([("grain", "fore", "aft", 4), ("grain", "fore", "mid", 2)])
    assert state(ship) == before


def test_a_hold_not_in_use_in_a_later_move(ship):
    ship.load("aft", "wool", 1)
    ship.seal_hold("aft", "mid")
    before = state(ship)
    with pytest.raises(KeyError):
        ship.apply_moves([("grain", "fore", "mid", 1), ("grain", "fore", "aft", 1)])
    with pytest.raises(KeyError):
        ship.apply_moves([("grain", "fore", "mid", 1), ("coal", "bow", "fore", 1)])
    assert state(ship) == before


@pytest.mark.parametrize("count", [0, -2])
def test_a_count_of_0_or_less_in_a_later_move(ship, count):
    before = state(ship)
    with pytest.raises(ValueError):
        ship.apply_moves([("grain", "fore", "mid", 1), ("steel", "fore", "aft", count)])
    assert state(ship) == before


def test_the_same_hold_on_both_sides_in_a_later_move(ship):
    before = state(ship)
    with pytest.raises(ValueError):
        ship.apply_moves([("grain", "fore", "mid", 1), ("coal", "mid", "mid", 1)])
    assert state(ship) == before


def test_a_failed_plan_leaves_the_ship_usable(ship):
    with pytest.raises(NotEnoughCrates):
        ship.apply_moves([("grain", "fore", "aft", 5), ("grain", "fore", "aft", 1)])
    assert ship.apply_moves([("grain", "fore", "aft", 5)]) == 5
    assert ship.get_count("aft", "grain") == 5
    assert ship.get_cargo("fore") == ["steel"]
