"""Hidden tests for the c_lowstock change (stock and order look-ups). Never
shown to the writer or the editor.

Usage (with warehouse.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lowstock/private/test_lowstock_new.py
"""

import pytest
from warehouse import OutOfStock, Warehouse


@pytest.fixture
def warehouse():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.add_product("nut")
    wh.add_product("washer")
    wh.receive("bolt", 100)
    wh.receive("nut", 10)
    wh.place_order("bolt", 40)  # order 1
    wh.place_order("nut", 10)  # order 2
    wh.place_order("bolt", 25)  # order 3
    return wh


def test_low_stock_is_strictly_below_the_threshold(warehouse):
    # stocks: bolt 35, nut 0, washer 0
    assert warehouse.get_low_stock(35) == ["nut", "washer"]
    assert warehouse.get_low_stock(36) == ["bolt", "nut", "washer"]
    assert warehouse.get_low_stock(1) == ["nut", "washer"]


def test_low_stock_with_threshold_zero_is_empty(warehouse):
    assert warehouse.get_low_stock(0) == []


def test_low_stock_keeps_the_order_products_were_added(warehouse):
    warehouse.receive("nut", 5)
    assert warehouse.get_low_stock(1000) == ["bolt", "nut", "washer"]


def test_low_stock_follows_deliveries_and_orders(warehouse):
    warehouse.receive("washer", 3)
    assert warehouse.get_low_stock(3) == ["nut"]
    warehouse.place_order("washer", 1)
    assert warehouse.get_low_stock(3) == ["nut", "washer"]


def test_an_empty_warehouse_has_no_low_stock():
    assert Warehouse().get_low_stock(5) == []


@pytest.mark.parametrize("threshold", [-1, 2.5, "5", None, True])
def test_invalid_thresholds_are_rejected(warehouse, threshold):
    with pytest.raises(ValueError):
        warehouse.get_low_stock(threshold)


def test_orders_are_listed_per_product_in_placement_order(warehouse):
    assert warehouse.get_orders("bolt") == [1, 3]
    assert warehouse.get_orders("nut") == [2]
    assert warehouse.get_orders("washer") == []
    warehouse.place_order("bolt", 5)
    assert warehouse.get_orders("bolt") == [1, 3, 4]


def test_failed_orders_are_not_listed(warehouse):
    with pytest.raises(OutOfStock):
        warehouse.place_order("nut", 1)
    assert warehouse.get_orders("nut") == [2]
    assert warehouse.get_large_orders(1) == [1, 2, 3]


@pytest.mark.parametrize("sku", ["screw", None, 7])
def test_orders_of_an_unknown_product_raise_key_error(warehouse, sku):
    with pytest.raises(KeyError):
        warehouse.get_orders(sku)


def test_large_orders_include_the_minimum_itself(warehouse):
    assert warehouse.get_large_orders(25) == [1, 3]
    assert warehouse.get_large_orders(26) == [1]
    assert warehouse.get_large_orders(10) == [1, 2, 3]
    assert warehouse.get_large_orders(41) == []


@pytest.mark.parametrize("min_quantity", [0, -3, 1.5, "2", None, True])
def test_invalid_minimum_quantities_are_rejected(warehouse, min_quantity):
    with pytest.raises(ValueError):
        warehouse.get_large_orders(min_quantity)
