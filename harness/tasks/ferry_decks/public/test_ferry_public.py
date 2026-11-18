"""Public checks for ferry.py.

Usage (with ferry.py importable, e.g. in the sandbox):
    python -m pytest public/test_ferry_public.py
"""

import pytest
from ferry import Ferry, FerryError


@pytest.fixture
def ferry():
    f = Ferry()
    f.add_deck("upper")
    f.add_deck("lower")
    return f


def test_vehicles_are_listed_in_the_order_they_boarded(ferry):
    ferry.board("van", "upper")
    ferry.board("bus", "upper")
    ferry.board("bike", "lower")
    assert ferry.get_vehicles("upper") == ["van", "bus"]
    assert ferry.get_vehicles("lower") == ["bike"]
    assert ferry.get_deck_of("bus") == "upper"


def test_a_vehicle_already_aboard_cannot_board_again(ferry):
    ferry.board("van", "upper")
    with pytest.raises(FerryError):
        ferry.board("van", "lower")
    assert ferry.get_vehicles("upper") == ["van"]
    assert ferry.get_vehicles("lower") == []


def test_leaving_keeps_the_order_of_the_others(ferry):
    for vehicle in ["van", "bus", "truck"]:
        ferry.board(vehicle, "upper")
    ferry.leave("bus")
    assert ferry.get_vehicles("upper") == ["van", "truck"]
    with pytest.raises(KeyError):
        ferry.get_deck_of("bus")


def test_move_vehicle_puts_it_at_the_end_of_the_other_deck(ferry):
    ferry.board("van", "upper")
    ferry.board("bus", "upper")
    ferry.board("bike", "lower")
    ferry.move_vehicle("van", "lower")
    assert ferry.get_vehicles("upper") == ["bus"]
    assert ferry.get_vehicles("lower") == ["bike", "van"]
    assert ferry.get_deck_of("van") == "lower"


def test_move_deck_moves_every_vehicle_in_order(ferry):
    for vehicle in ["van", "bus", "truck"]:
        ferry.board(vehicle, "upper")
    assert ferry.move_deck("upper", "lower") == 3
    assert ferry.get_vehicles("upper") == []
    assert ferry.get_vehicles("lower") == ["van", "bus", "truck"]


def test_unload_deck_returns_the_vehicles_in_order(ferry):
    ferry.board("van", "upper")
    ferry.board("bus", "upper")
    assert ferry.unload_deck("upper") == ["van", "bus"]
    assert ferry.get_vehicles("upper") == []
    with pytest.raises(KeyError):
        ferry.get_deck_of("van")
    ferry.board("van", "upper")
    assert ferry.get_vehicles("upper") == ["van"]
