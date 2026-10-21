"""Public checks for the c_returns change (returning orders). Shown to the
editor, never to the writer.

Usage (with warehouse.py importable, e.g. in the sandbox):
    python -m pytest changes/c_returns/public/test_returns_public.py
"""

import pytest
from warehouse import Warehouse, WarehouseError


def test_returning_an_order_puts_the_units_back():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.receive("bolt", 100)
    order = wh.place_order("bolt", 30)
    assert not wh.is_returned(order)
    wh.return_order(order)
    assert wh.is_returned(order)
    assert wh.get_stock("bolt") == 100
    assert wh.get_history("bolt") == [("received", 100), ("ordered", 30), ("returned", 30)]


def test_an_order_can_only_be_returned_once():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.receive("bolt", 10)
    order = wh.place_order("bolt", 4)
    wh.return_order(order)
    with pytest.raises(WarehouseError):
        wh.return_order(order)
    assert wh.get_stock("bolt") == 10
