"""Public checks for the c_board_many change (a group boards as a whole).
Shown to the editor, never to the writer.

Usage (with ferry.py importable, e.g. in the sandbox):
    python -m pytest changes/c_board_many/public/test_ferry_board_many_public.py
"""

import pytest
from ferry import Ferry, FerryError


@pytest.fixture
def ferry():
    f = Ferry()
    f.add_deck("upper")
    f.add_deck("lower")
    f.board("van", "upper")
    return f


def test_board_many_boards_every_vehicle_in_order(ferry):
    assert ferry.board_many([("bus", "upper"), ("bike", "lower"), ("car", "upper")]) == 3
    assert ferry.get_vehicles("upper") == ["van", "bus", "car"]
    assert ferry.get_vehicles("lower") == ["bike"]


def test_board_many_with_one_vehicle_aboard_boards_none(ferry):
    with pytest.raises(FerryError):
        ferry.board_many([("bus", "lower"), ("van", "lower")])
    assert ferry.get_vehicles("lower") == []
    with pytest.raises(KeyError):
        ferry.get_deck_of("bus")
