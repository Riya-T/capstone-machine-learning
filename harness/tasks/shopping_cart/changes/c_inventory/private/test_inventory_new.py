import pytest

from cart import ShoppingCart


def test_stock_limit_can_be_filled_exactly():
    cart = ShoppingCart(stock_inventory={"SKU": 4})
    cart.add_item("SKU", "Widget", 3.0, 2)
    cart.add_item("SKU", "Widget", 3.0, 2)
    assert cart.get_total() == 12.0


def test_exceeding_stock_raises_and_leaves_existing_quantity_unchanged():
    cart = ShoppingCart(stock_inventory={"SKU": 5})
    cart.add_item("SKU", "Limited item", 10.0, 4)
    with pytest.raises(ValueError):
        cart.add_item("SKU", "Limited item", 10.0, 2)
    assert cart.get_total() == 40.0


def test_stock_failure_does_not_add_a_new_item():
    cart = ShoppingCart(stock_inventory={"SKU": 0})
    with pytest.raises(ValueError):
        cart.add_item("SKU", "Unavailable", 10.0)
    assert cart.get_total() == 0.0


def test_removing_quantity_allows_it_to_be_added_again():
    cart = ShoppingCart(stock_inventory={"SKU": 2})
    cart.add_item("SKU", "Widget", 3.0, 2)
    cart.remove_item("SKU")
    cart.add_item("SKU", "Widget", 3.0)
    assert cart.get_total() == 6.0


def test_stock_limits_are_independent_per_item():
    cart = ShoppingCart(stock_inventory={"A": 1, "B": 2})
    cart.add_item("A", "Item A", 4.0)
    cart.add_item("B", "Item B", 5.0, 2)
    assert cart.get_total() == 14.0
    with pytest.raises(ValueError):
        cart.add_item("A", "Item A", 4.0)


def test_removed_units_free_stock_for_later_additions():
    cart = ShoppingCart(stock_inventory={"SKU": 2})
    cart.add_item("SKU", "Widget", 3.0, 2)
    cart.remove_item("SKU", 2)
    cart.add_item("SKU", "Widget", 3.0, 2)
    assert cart.get_total() == 6.0
