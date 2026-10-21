"""Public checks for the c_bundle change (all-or-nothing bundles). Shown to
the editor, never to the writer.

Usage (with warehouse.py importable, e.g. in the sandbox):
    python -m pytest changes/c_bundle/public/test_bundle_public.py
"""

import pytest
from warehouse import OutOfStock, Warehouse


@pytest.fixture
def warehouse():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.add_product("nut")
    wh.receive("bolt", 100)
    wh.receive("nut", 10)
    return wh


def test_a_bundle_makes_one_order_per_line(warehouse):
    ids = warehouse.place_bundle([("bolt", 30), ("nut", 5)])
    assert ids == [1, 2]
    assert warehouse.get_order(1) == ("bolt", 30)
    assert warehouse.get_order(2) == ("nut", 5)
    assert warehouse.get_stock("bolt") == 70
    assert warehouse.get_stock("nut") == 5


def test_a_bundle_that_cannot_be_covered_takes_nothing(warehouse):
    with pytest.raises(OutOfStock):
        warehouse.place_bundle([("bolt", 30), ("nut", 11)])
    assert warehouse.get_stock("bolt") == 100
    assert warehouse.get_stock("nut") == 10
    assert warehouse.get_history("bolt") == [("received", 100)]
