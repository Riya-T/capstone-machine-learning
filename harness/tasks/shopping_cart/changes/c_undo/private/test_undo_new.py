import pytest

from cart import ShoppingCart


def test_empty_undo_returns_false():
    assert ShoppingCart().undo() is False


def test_undoes_successful_operations_in_reverse_order():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 2.0, 2)
    cart.add_item("B", "Bread", 3.0)
    cart.remove_item("A")

    assert cart.undo() is True
    assert cart.get_total() == 7.0
    assert cart.undo() is True
    assert cart.get_total() == 4.0
    assert cart.undo() is True
    assert cart.get_total() == 0.0
    assert cart.undo() is False


def test_undo_restores_entirely_removed_item():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 2.0, 2)
    cart.remove_item("A", 5)
    assert cart.get_total() == 0.0
    assert cart.undo() is True
    assert cart.get_total() == 4.0


def test_invalid_and_no_op_operations_do_not_create_history_entries():
    cart = ShoppingCart()
    cart.remove_item("missing")
    with pytest.raises(ValueError):
        cart.remove_item("missing", 0)
    assert cart.undo() is False


def test_invalid_removal_does_not_hide_a_prior_successful_operation():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 2.0, 2)
    with pytest.raises(ValueError):
        cart.remove_item("A", 0)
    assert cart.undo() is True
    assert cart.get_total() == 0.0


def test_undoing_an_add_to_existing_item_restores_previous_quantity():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 2.0, 2)
    cart.add_item("A", "Apple", 2.0, 3)
    assert cart.undo() is True
    assert cart.get_total() == 4.0


def test_undoing_partial_removal_restores_previous_total():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 2.0, 4)
    cart.remove_item("A", 1)
    assert cart.undo() is True
    assert cart.get_total() == 8.0


def test_undo_does_not_remove_an_older_history_entry():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 2.0)
    cart.add_item("B", "Bread", 3.0)
    assert cart.undo() is True
    assert cart.get_total() == 2.0
    cart.add_item("C", "Cake", 4.0)
    assert cart.undo() is True
    assert cart.get_total() == 2.0
    assert cart.undo() is True
    assert cart.get_total() == 0.0


def test_discount_remains_applied_when_cart_contents_are_undone():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 10.0, 2)
    cart.apply_discount_code("SAVE10")
    cart.add_item("B", "Bread", 5.0)
    assert cart.undo() is True
    assert cart.get_total() == 18.0


def test_undo_can_remove_the_only_item_from_a_new_cart():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 4.0)
    assert cart.undo() is True
    assert cart.get_total() == 0.0


def test_undo_after_removing_missing_item_returns_false():
    cart = ShoppingCart()
    cart.remove_item("missing")
    assert cart.undo() is False


def test_undo_removal_restores_only_removed_line_and_preserves_other_items():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 2.0, 2)
    cart.add_item("B", "Bread", 3.0)
    cart.remove_item("A", 2)
    assert cart.undo() is True
    assert cart.get_total() == 7.0


def test_no_op_removal_does_not_hide_last_successful_change():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 2.0)
    cart.remove_item("missing")
    assert cart.undo() is True
    assert cart.get_total() == 0.0


def test_coupon_total_is_recalculated_after_undo_restores_item():
    cart = ShoppingCart()
    cart.add_item("A", "Apple", 10.0, 2)
    cart.apply_discount_code("SAVE10")
    cart.remove_item("A", 1)
    assert cart.undo() is True
    assert cart.get_total() == 18.0
