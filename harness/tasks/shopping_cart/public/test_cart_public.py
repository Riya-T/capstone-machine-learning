from cart import ShoppingCart


def test_adding_items_and_getting_total():
    cart = ShoppingCart()
    cart.add_item("book", "Book", 12.5)
    cart.add_item("pen", "Pen", 1.0)
    assert cart.get_total() == 13.5


def test_empty_cart_total_is_zero():
    cart = ShoppingCart()
    assert cart.get_total() == 0.0


def test_removing_unknown_item_leaves_total_unchanged():
    cart = ShoppingCart()
    cart.add_item("book", "Book", 12.5)
    cart.add_item("pen", "Pen", 1.0)
    cart.remove_item("missing")
    assert cart.get_total() == 13.5
