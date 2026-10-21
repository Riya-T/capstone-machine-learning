"""Hidden tests for the c_discounts change (coupon discounts). Never shown to
the writer or the editor.

Usage (with cart.py importable, e.g. in the sandbox):
    python -m pytest changes/c_discounts/private/test_discounts_new.py
"""

import pytest

from cart import ShoppingCart


def test_coupon_can_be_applied_before_adding_items():
    cart = ShoppingCart()
    cart.apply_discount_code("SAVE10")
    cart.add_item("A", "A", 10.0, 2)
    assert cart.get_total() == 18.0


def test_reapplying_coupon_does_not_compound_discount():
    cart = ShoppingCart()
    cart.add_item("A", "A", 100.0)
    cart.apply_discount_code("SAVE10")
    cart.apply_discount_code("SAVE10")
    assert cart.get_total() == 90.0


def test_invalid_coupon_does_not_replace_existing_discount():
    cart = ShoppingCart()
    cart.add_item("A", "A", 50.0)
    cart.apply_discount_code("SAVE10")
    with pytest.raises(ValueError):
        cart.apply_discount_code("INVALID")
    assert cart.get_total() == 45.0


def test_discounted_total_tracks_item_changes():
    cart = ShoppingCart()
    cart.add_item("A", "A", 10.0, 3)
    cart.apply_discount_code("SAVE10")
    cart.remove_item("A", 1)
    assert cart.get_total() == 18.0


def test_discount_on_empty_cart_keeps_zero_total():
    cart = ShoppingCart()
    cart.apply_discount_code("SAVE10")
    assert cart.get_total() == 0.0


def test_discount_applies_to_all_items_and_quantities():
    cart = ShoppingCart()
    cart.add_item("A", "A", 10.0, 2)
    cart.add_item("B", "B", 5.0, 4)
    cart.apply_discount_code("SAVE10")
    assert cart.get_total() == 36.0


def test_invalid_code_on_fresh_cart_keeps_full_total():
    cart = ShoppingCart()
    cart.add_item("A", "A", 25.0)
    with pytest.raises(ValueError):
        cart.apply_discount_code("save10")
    assert cart.get_total() == 25.0
