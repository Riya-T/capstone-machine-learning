"""Hidden tests for the c_board_many change (a group boards as a whole).
Never shown to the writer or the editor.

Usage (with ferry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_board_many/private/test_ferry_board_many_new.py
"""

import pytest
from ferry import Ferry, FerryError

DECKS = ["upper", "lower", "hold"]


@pytest.fixture
def ferry():
    f = Ferry()
    for name in DECKS:
        f.add_deck(name)
    f.board("van", "upper")
    f.board("bus", "upper")
    f.board("bike", "lower")
    return f


def state(f, decks=DECKS):
    return [(d, f.get_vehicles(d)) for d in decks]


# --- groups that board ------------------------------------------------------------


def test_board_many_of_one_vehicle_is_like_board(ferry):
    assert ferry.board_many([("car", "lower")]) == 1
    assert ferry.get_vehicles("lower") == ["bike", "car"]
    assert ferry.get_deck_of("car") == "lower"


def test_board_many_onto_several_decks(ferry):
    assert ferry.board_many([("car", "hold"), ("lorry", "upper"), ("camper", "hold")]) == 3
    assert state(ferry) == [
        ("upper", ["van", "bus", "lorry"]),
        ("lower", ["bike"]),
        ("hold", ["car", "camper"]),
    ]
    assert [ferry.get_deck_of(v) for v in ["car", "lorry", "camper"]] == ["hold", "upper", "hold"]


def test_board_many_vehicles_can_then_move_and_leave(ferry):
    ferry.board_many([("car", "hold"), ("lorry", "hold")])
    ferry.move_vehicle("car", "upper")
    ferry.leave("lorry")
    assert state(ferry) == [("upper", ["van", "bus", "car"]), ("lower", ["bike"]), ("hold", [])]


def test_board_many_after_a_vehicle_left(ferry):
    ferry.leave("van")
    assert ferry.board_many([("van", "hold"), ("car", "hold")]) == 2
    assert ferry.get_vehicles("hold") == ["van", "car"]
    assert ferry.get_vehicles("upper") == ["bus"]


def test_board_many_of_vehicles_from_an_unloaded_deck(ferry):
    ferry.unload_deck("upper")
    assert ferry.board_many([("bus", "lower"), ("van", "lower")]) == 2
    assert ferry.get_vehicles("lower") == ["bike", "bus", "van"]


def test_board_many_vehicles_count_as_aboard_for_later_calls(ferry):
    ferry.board_many([("car", "hold"), ("lorry", "lower")])
    with pytest.raises(FerryError):
        ferry.board("lorry", "upper")
    assert ferry.unload_deck("hold") == ["car"]


# --- groups that board as a whole or not at all -----------------------------------


def test_board_many_with_the_last_vehicle_aboard_changes_nothing(ferry):
    before = state(ferry)
    with pytest.raises(FerryError):
        ferry.board_many([("car", "hold"), ("lorry", "lower"), ("bike", "hold")])
    assert state(ferry) == before
    for vehicle in ["car", "lorry"]:
        with pytest.raises(KeyError):
            ferry.get_deck_of(vehicle)


def test_board_many_with_a_name_twice_changes_nothing(ferry):
    before = state(ferry)
    with pytest.raises(FerryError):
        ferry.board_many([("car", "hold"), ("lorry", "hold"), ("car", "upper")])
    assert state(ferry) == before


def test_board_many_with_a_deck_never_added_changes_nothing(ferry):
    before = state(ferry)
    with pytest.raises(KeyError):
        ferry.board_many([("car", "hold"), ("lorry", "attic")])
    assert state(ferry) == before
    with pytest.raises(KeyError):
        ferry.get_deck_of("car")


def test_board_many_that_failed_can_be_retried_once_fixed(ferry):
    with pytest.raises(FerryError):
        ferry.board_many([("car", "hold"), ("bus", "hold")])
    ferry.leave("bus")
    assert ferry.board_many([("car", "hold"), ("bus", "hold")]) == 2
    assert state(ferry) == [("upper", ["van"]), ("lower", ["bike"]), ("hold", ["car", "bus"])]
