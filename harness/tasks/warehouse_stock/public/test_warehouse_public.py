"""Public checks for warehouse.py.

Usage (with warehouse.py importable, e.g. in the sandbox):
    python -m pytest public/test_warehouse_public.py
"""

import pytest
from warehouse import OutOfStock, Warehouse


@pytest.fixture
def warehouse():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.add_product("nut")
    return wh


def test_receiving_adds_to_the_stock(warehouse):
    warehouse.receive("bolt", 100)
    warehouse.receive("bolt", 50)
    assert warehouse.get_stock("bolt") == 150
    assert warehouse.get_stock("nut") == 0


def test_an_order_takes_stock_out_and_gets_an_id(warehouse):
    warehouse.receive("bolt", 100)
    assert warehouse.place_order("bolt", 30) == 1
    assert warehouse.place_order("bolt", 20) == 2
    assert warehouse.get_stock("bolt") == 50
    assert warehouse.get_order(2) == ("bolt", 20)


def test_ordering_more_than_the_stock_raises(warehouse):
    warehouse.receive("bolt", 10)
    with pytest.raises(OutOfStock):
        warehouse.place_order("bolt", 11)
    assert warehouse.get_stock("bolt") == 10


def test_history_records_each_movement(warehouse):
    warehouse.receive("bolt", 100)
    warehouse.place_order("bolt", 30)
    assert warehouse.get_history("bolt") == [("received", 100), ("ordered", 30)]
    assert warehouse.get_history("nut") == []


def test_quantities_must_be_positive(warehouse):
    with pytest.raises(ValueError):
        warehouse.receive("bolt", 0)
    with pytest.raises(ValueError):
        warehouse.receive("bolt", -5)


def test_unknown_product_raises_key_error(warehouse):
    with pytest.raises(KeyError):
        warehouse.get_stock("washer")
