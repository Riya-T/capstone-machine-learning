"""Hidden tests for the c_bundle change (all-or-nothing bundles). Never
shown to the writer or the editor.

Usage (with warehouse.py importable, e.g. in the sandbox):
    python -m pytest changes/c_bundle/private/test_bundle_new.py
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
    return wh


def state(wh):
    return {s: (wh.get_stock(s), wh.get_history(s)) for s in wh.get_products()}


def test_bundle_ids_follow_earlier_orders_in_line_order(warehouse):
    warehouse.place_order("bolt", 1)
    ids = warehouse.place_bundle([("nut", 2), ("bolt", 3)])
    assert ids == [2, 3]
    assert warehouse.get_order(2) == ("nut", 2)
    assert warehouse.get_order(3) == ("bolt", 3)
    assert warehouse.place_order("bolt", 1) == 4


def test_a_bundle_writes_history_like_single_orders(warehouse):
    warehouse.place_bundle([("bolt", 30), ("nut", 5)])
    assert warehouse.get_history("bolt") == [("received", 100), ("ordered", 30)]
    assert warehouse.get_history("nut") == [("received", 10), ("ordered", 5)]
    assert warehouse.get_history("washer") == []


def test_a_single_line_bundle_works(warehouse):
    assert warehouse.place_bundle([("nut", 10)]) == [1]
    assert warehouse.get_stock("nut") == 0


def test_a_bundle_may_take_the_whole_stock(warehouse):
    warehouse.place_bundle([("bolt", 100), ("nut", 10)])
    assert (warehouse.get_stock("bolt"), warehouse.get_stock("nut")) == (0, 0)


def test_an_empty_bundle_is_rejected(warehouse):
    before = state(warehouse)
    with pytest.raises(ValueError):
        warehouse.place_bundle([])
    assert state(warehouse) == before


def test_an_unknown_sku_anywhere_in_the_bundle_takes_nothing(warehouse):
    before = state(warehouse)
    with pytest.raises(KeyError):
        warehouse.place_bundle([("bolt", 5), ("screw", 1)])
    with pytest.raises(KeyError):
        warehouse.place_bundle([(None, 5), ("bolt", 1)])
    assert state(warehouse) == before
    assert warehouse.place_order("bolt", 1) == 1


@pytest.mark.parametrize("quantity", [0, -1, 2.5, "3", None])
def test_a_bad_quantity_anywhere_in_the_bundle_takes_nothing(warehouse, quantity):
    before = state(warehouse)
    with pytest.raises(ValueError):
        warehouse.place_bundle([("bolt", 5), ("nut", quantity)])
    assert state(warehouse) == before


def test_a_repeated_sku_is_rejected(warehouse):
    before = state(warehouse)
    with pytest.raises(ValueError):
        warehouse.place_bundle([("bolt", 5), ("nut", 1), ("bolt", 5)])
    assert state(warehouse) == before


def test_a_short_line_fails_the_whole_bundle_even_when_earlier_lines_fit(warehouse):
    before = state(warehouse)
    with pytest.raises(OutOfStock):
        warehouse.place_bundle([("bolt", 1), ("nut", 11)])
    with pytest.raises(OutOfStock):
        warehouse.place_bundle([("washer", 1), ("bolt", 1)])
    assert state(warehouse) == before
    assert warehouse.place_order("bolt", 1) == 1


def test_bundle_errors_are_reported_in_order(warehouse):
    with pytest.raises(KeyError):
        warehouse.place_bundle([("bolt", 0), ("screw", -1), ("bolt", 1000)])
    with pytest.raises(ValueError):
        warehouse.place_bundle([("bolt", 0), ("bolt", 1000)])
    with pytest.raises(ValueError):
        warehouse.place_bundle([("bolt", 1000), ("bolt", 1)])


def test_each_order_of_a_bundle_can_be_returned_on_its_own(warehouse):
    ids = warehouse.place_bundle([("bolt", 30), ("nut", 5)])
    warehouse.return_order(ids[1])
    assert warehouse.get_stock("bolt") == 70
    assert warehouse.get_stock("nut") == 10
    assert warehouse.is_returned(ids[1])
    assert not warehouse.is_returned(ids[0])
    assert warehouse.get_history("nut")[-1] == ("returned", 5)
