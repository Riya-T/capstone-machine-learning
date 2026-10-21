"""Hidden tests for the c_returns change (returning orders). Never shown to
the writer or the editor.

Usage (with warehouse.py importable, e.g. in the sandbox):
    python -m pytest changes/c_returns/private/test_returns_new.py
"""

import pytest
from warehouse import OutOfStock, Warehouse, WarehouseError


@pytest.fixture
def warehouse():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.add_product("nut")
    wh.receive("bolt", 100)
    wh.receive("nut", 50)
    wh.place_order("bolt", 30)  # order 1
    wh.place_order("nut", 50)  # order 2
    wh.place_order("bolt", 20)  # order 3
    return wh


def state(wh, order_ids=(1, 2, 3)):
    products = {s: (wh.get_stock(s), wh.get_history(s)) for s in wh.get_products()}
    return products, [(wh.get_order(o), wh.is_returned(o)) for o in order_ids]


def test_new_orders_are_not_returned(warehouse):
    assert [warehouse.is_returned(o) for o in (1, 2, 3)] == [False, False, False]


def test_a_return_restores_the_stock_of_its_product_only(warehouse):
    warehouse.return_order(1)
    assert warehouse.get_stock("bolt") == 80
    assert warehouse.get_stock("nut") == 0
    assert warehouse.is_returned(1)
    assert not warehouse.is_returned(3)


def test_a_return_is_recorded_in_the_history(warehouse):
    warehouse.return_order(3)
    assert warehouse.get_history("bolt") == [
        ("received", 100),
        ("ordered", 30),
        ("ordered", 20),
        ("returned", 20),
    ]
    assert warehouse.get_history("nut") == [("received", 50), ("ordered", 50)]


def test_returned_units_can_be_ordered_again(warehouse):
    with pytest.raises(OutOfStock):
        warehouse.place_order("nut", 1)
    warehouse.return_order(2)
    assert warehouse.place_order("nut", 50) == 4
    assert warehouse.get_stock("nut") == 0


def test_a_returned_order_keeps_its_id_and_details(warehouse):
    warehouse.return_order(1)
    assert warehouse.get_order(1) == ("bolt", 30)
    assert warehouse.place_order("bolt", 1) == 4
    assert warehouse.get_order(4) == ("bolt", 1)


def test_returning_twice_raises_and_changes_nothing(warehouse):
    warehouse.return_order(1)
    before = state(warehouse)
    with pytest.raises(WarehouseError):
        warehouse.return_order(1)
    assert state(warehouse) == before


def test_other_orders_can_still_be_returned_after_one_is(warehouse):
    warehouse.return_order(1)
    warehouse.return_order(3)
    assert warehouse.get_stock("bolt") == 100
    assert [warehouse.is_returned(o) for o in (1, 2, 3)] == [True, False, True]


@pytest.mark.parametrize("order_id", [0, 99, None, "1"])
def test_unknown_order_ids_raise_key_error(warehouse, order_id):
    before = state(warehouse)
    with pytest.raises(KeyError):
        warehouse.return_order(order_id)
    with pytest.raises(KeyError):
        warehouse.is_returned(order_id)
    assert state(warehouse) == before


def test_a_return_does_not_count_as_a_delivery(warehouse):
    warehouse.return_order(2)
    assert ("received", 50) in warehouse.get_history("nut")
    assert warehouse.get_history("nut").count(("received", 50)) == 1
    assert warehouse.get_history("nut")[-1] == ("returned", 50)
