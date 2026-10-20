import pytest

from cart import ShoppingCart


def test_save10_reduces_the_total_by_ten_percent():
    cart = ShoppingCart()
    cart.add_item("X1", "Book", 20.0, 2)
    cart.apply_discount_code("SAVE10")
    assert cart.get_total() == 36.0


def test_invalid_code_is_rejected():
    cart = ShoppingCart()
    with pytest.raises(ValueError):
        cart.apply_discount_code("NOT-A-COUPON")
