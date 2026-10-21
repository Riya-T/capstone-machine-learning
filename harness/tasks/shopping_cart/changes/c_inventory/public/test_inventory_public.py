"""Public checks for the c_inventory change (stock limits). Shown to the
editor, never to the writer.

Usage (with cart.py importable, e.g. in the sandbox):
    python -m pytest changes/c_inventory/public/test_inventory_public.py
"""

import pytest

from cart import ShoppingCart


def test_stock_limit_applies_across_multiple_additions():
    cart = ShoppingCart(stock_inventory={"SKU1": 3})
    cart.add_item("SKU1", "Shoes", 50.0, quantity=2)
    with pytest.raises(ValueError):
        cart.add_item("SKU1", "Shoes", 50.0, quantity=2)
    assert cart.get_total() == 100.0


def test_items_without_a_stock_entry_are_unlimited():
    cart = ShoppingCart(stock_inventory={"SKU1": 1})
    cart.add_item("OTHER", "Notebook", 2.0, quantity=10)
    assert cart.get_total() == 20.0
