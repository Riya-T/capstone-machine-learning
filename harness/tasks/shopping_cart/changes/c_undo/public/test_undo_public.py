from cart import ShoppingCart


def test_undo_reverts_the_last_add():
    cart = ShoppingCart()
    cart.add_item("P1", "Pen", 2.0, 3)
    cart.add_item("P2", "Notebook", 5.0)
    assert cart.undo() is True
    assert cart.get_total() == 6.0


def test_undo_of_remove_restores_removed_quantity():
    cart = ShoppingCart()
    cart.add_item("P1", "Pen", 2.0, 3)
    cart.remove_item("P1", 2)
    assert cart.undo() is True
    assert cart.get_total() == 6.0
