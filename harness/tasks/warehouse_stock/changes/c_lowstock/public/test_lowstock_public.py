"""Public checks for the c_lowstock change (stock and order look-ups). Shown
to the editor, never to the writer.

Usage (with warehouse.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lowstock/public/test_lowstock_public.py
"""

from warehouse import Warehouse


def test_low_stock_lists_products_below_the_threshold():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.add_product("nut")
    wh.add_product("washer")
    wh.receive("bolt", 100)
    wh.receive("nut", 10)
    assert wh.get_low_stock(10) == ["washer"]
    assert wh.get_low_stock(11) == ["nut", "washer"]
    assert wh.get_low_stock(0) == []


def test_orders_can_be_found_by_product_and_by_size():
    wh = Warehouse()
    wh.add_product("bolt")
    wh.add_product("nut")
    wh.receive("bolt", 100)
    wh.receive("nut", 100)
    wh.place_order("bolt", 10)
    wh.place_order("nut", 40)
    wh.place_order("bolt", 50)
    assert wh.get_orders("bolt") == [1, 3]
    assert wh.get_orders("nut") == [2]
    assert wh.get_large_orders(40) == [2, 3]
