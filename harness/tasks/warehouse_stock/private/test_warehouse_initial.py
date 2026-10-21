"""Hidden tests for the initial warehouse_stock spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with warehouse.py importable, e.g. in the sandbox):
    python -m pytest private/test_warehouse_initial.py
"""

import pytest
from warehouse import OutOfStock, Warehouse, WarehouseError

BAD_QUANTITIES = [0, -5, 1.5, "10", None]
BAD_IDS = [0, 99, -1, None, "1"]


@pytest.fixture
def warehouse():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.add_product("nut")
    return wh


def state(wh, order_ids=()):
    """Every stock and history, plus the given orders, to check that a failed
    call changed nothing."""
    products = {s: (wh.get_stock(s), wh.get_history(s)) for s in wh.get_products()}
    return products, [wh.get_order(o) for o in order_ids]


# --- products ---------------------------------------------------------------


def test_a_new_product_has_no_stock_and_no_history(warehouse):
    assert warehouse.get_stock("bolt") == 0
    assert warehouse.get_history("bolt") == []


def test_products_are_listed_in_the_order_added():
    wh = Warehouse()
    for sku in ["washer", "bolt", "nut"]:
        wh.add_product(sku)
    assert wh.get_products() == ["washer", "bolt", "nut"]


@pytest.mark.parametrize("bad_sku", [""])
def test_invalid_skus_are_rejected(bad_sku):
    wh = Warehouse()
    with pytest.raises(ValueError):
        wh.add_product(bad_sku)
    assert wh.get_products() == []


def test_adding_an_existing_product_is_rejected(warehouse):
    warehouse.receive("bolt", 40)
    with pytest.raises(WarehouseError):
        warehouse.add_product("bolt")
    assert warehouse.get_stock("bolt") == 40
    assert warehouse.get_products() == ["bolt", "nut"]


@pytest.mark.parametrize(
    "call",
    [
        lambda wh: wh.receive("washer", 10),
        lambda wh: wh.place_order("washer", 10),
        lambda wh: wh.get_stock("washer"),
        lambda wh: wh.get_history("washer"),
        lambda wh: wh.get_stock(None),
        lambda wh: wh.get_stock(7),
        lambda wh: wh.receive(None, 10),
    ],
)
def test_skus_that_are_not_products_raise_key_error(warehouse, call):
    warehouse.receive("bolt", 20)
    before = state(warehouse)
    with pytest.raises(KeyError):
        call(warehouse)
    assert state(warehouse) == before


# --- stock ------------------------------------------------------------------


def test_deliveries_and_orders_change_the_stock(warehouse):
    warehouse.receive("bolt", 100)
    warehouse.receive("bolt", 25)
    warehouse.place_order("bolt", 60)
    assert warehouse.get_stock("bolt") == 65
    assert warehouse.get_stock("nut") == 0


def test_the_whole_stock_can_be_ordered(warehouse):
    warehouse.receive("bolt", 30)
    warehouse.place_order("bolt", 30)
    assert warehouse.get_stock("bolt") == 0


def test_ordering_from_an_empty_product_raises(warehouse):
    before = state(warehouse)
    with pytest.raises(OutOfStock):
        warehouse.place_order("nut", 1)
    assert state(warehouse) == before


def test_ordering_more_than_the_stock_changes_nothing(warehouse):
    warehouse.receive("bolt", 30)
    before = state(warehouse)
    with pytest.raises(OutOfStock):
        warehouse.place_order("bolt", 31)
    assert state(warehouse) == before


def test_order_ids_count_up_from_one(warehouse):
    warehouse.receive("bolt", 100)
    warehouse.receive("nut", 100)
    assert warehouse.place_order("bolt", 10) == 1
    assert warehouse.place_order("nut", 10) == 2
    assert warehouse.place_order("bolt", 10) == 3


def test_a_failed_order_uses_no_id(warehouse):
    warehouse.receive("bolt", 10)
    with pytest.raises(OutOfStock):
        warehouse.place_order("bolt", 11)
    with pytest.raises(ValueError):
        warehouse.place_order("bolt", 0)
    assert warehouse.place_order("bolt", 5) == 1


def test_get_order_returns_sku_and_quantity(warehouse):
    warehouse.receive("bolt", 100)
    warehouse.receive("nut", 100)
    warehouse.place_order("bolt", 10)
    warehouse.place_order("nut", 25)
    assert warehouse.get_order(1) == ("bolt", 10)
    assert warehouse.get_order(2) == ("nut", 25)


@pytest.mark.parametrize("order_id", BAD_IDS)
def test_unknown_order_ids_raise_key_error(warehouse, order_id):
    warehouse.receive("bolt", 10)
    warehouse.place_order("bolt", 5)
    with pytest.raises(KeyError):
        warehouse.get_order(order_id)


@pytest.mark.parametrize("quantity", BAD_QUANTITIES)
@pytest.mark.parametrize(
    "call",
    [lambda wh, q: wh.receive("bolt", q), lambda wh, q: wh.place_order("bolt", q)],
    ids=["receive", "place_order"],
)
def test_invalid_quantities_are_rejected(warehouse, call, quantity):
    warehouse.receive("bolt", 100)
    before = state(warehouse)
    with pytest.raises(ValueError):
        call(warehouse, quantity)
    assert state(warehouse) == before


def test_a_missing_product_is_reported_before_a_bad_quantity(warehouse):
    with pytest.raises(KeyError):
        warehouse.receive("washer", -1)
    with pytest.raises(KeyError):
        warehouse.place_order("washer", 0)


def test_a_bad_quantity_is_reported_before_missing_stock(warehouse):
    # nut has 0 in stock, so 1.5 is also more than the stock.
    with pytest.raises(ValueError):
        warehouse.place_order("nut", 1.5)


# --- history ----------------------------------------------------------------


def test_history_lists_every_movement_oldest_first(warehouse):
    warehouse.receive("bolt", 100)
    warehouse.place_order("bolt", 30)
    warehouse.receive("bolt", 5)
    warehouse.place_order("bolt", 75)
    assert warehouse.get_history("bolt") == [
        ("received", 100),
        ("ordered", 30),
        ("received", 5),
        ("ordered", 75),
    ]
    assert warehouse.get_history("nut") == []


def test_products_have_separate_histories(warehouse):
    warehouse.receive("bolt", 10)
    warehouse.receive("nut", 20)
    assert warehouse.get_history("bolt") == [("received", 10)]
    assert warehouse.get_history("nut") == [("received", 20)]


def test_failed_calls_add_nothing_to_history(warehouse):
    warehouse.receive("bolt", 10)
    for call in (
        lambda: warehouse.place_order("bolt", 11),
        lambda: warehouse.receive("bolt", 0),
        lambda: warehouse.place_order("bolt", "3"),
    ):
        with pytest.raises((ValueError, WarehouseError)):
            call()
    assert warehouse.get_history("bolt") == [("received", 10)]


def test_out_of_stock_is_a_warehouse_error():
    assert issubclass(OutOfStock, WarehouseError)


def test_warehouses_do_not_share_products_or_orders():
    first, second = Warehouse(), Warehouse()
    first.add_product("bolt")
    first.receive("bolt", 5)
    first.place_order("bolt", 2)
    assert second.get_products() == []
    second.add_product("bolt")
    assert second.get_stock("bolt") == 0
    with pytest.raises(KeyError):
        second.get_order(1)
