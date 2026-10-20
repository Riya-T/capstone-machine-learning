import pytest

from cart import ShoppingCart


@pytest.fixture
def cart():
    return ShoppingCart()


def test_empty_cart_total_is_zero(cart):
    assert cart.get_total() == 0.0


def test_adding_first_item_sets_its_total(cart):
    cart.add_item("A1", "Apple", 1.5, 4)
    assert cart.get_total() == 6.0


def test_adding_multiple_items_sums_each_line_total(cart):
    cart.add_item("A1", "Apple", 1.5, 4)
    cart.add_item("B2", "Banana", 0.75, 2)
    assert cart.get_total() == 7.5


def test_readding_an_item_increases_quantity_without_changing_its_price(cart):
    cart.add_item("A1", "Apple", 1.5, 2)
    cart.add_item("A1", "Different name", 9.0, 3)
    assert cart.get_total() == 7.5


def test_removing_part_of_an_item_decreases_total(cart):
    cart.add_item("A1", "Apple", 1.5, 4)
    cart.remove_item("A1", 2)
    assert cart.get_total() == 3.0


def test_removing_at_least_the_remaining_quantity_removes_item(cart):
    cart.add_item("A1", "Apple", 1.5, 2)
    cart.remove_item("A1", 5)
    assert cart.get_total() == 0.0


def test_removing_unknown_item_does_nothing(cart):
    cart.add_item("A1", "Apple", 1.5, 2)
    cart.remove_item("missing")
    assert cart.get_total() == 3.0


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2"])
def test_add_rejects_invalid_quantity_without_changing_cart(cart, quantity):
    cart.add_item("A1", "Apple", 1.5, 2)
    with pytest.raises(ValueError):
        cart.add_item("B2", "Banana", 1.0, quantity)
    assert cart.get_total() == 3.0


@pytest.mark.parametrize("price", [-0.01, -3.0])
def test_add_rejects_negative_price_without_changing_cart(cart, price):
    cart.add_item("A1", "Apple", 1.5, 2)
    with pytest.raises(ValueError):
        cart.add_item("B2", "Banana", price)
    assert cart.get_total() == 3.0


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2"])
def test_remove_rejects_invalid_quantity_without_changing_cart(cart, quantity):
    cart.add_item("A1", "Apple", 1.5, 2)
    with pytest.raises(ValueError):
        cart.remove_item("A1", quantity)
    assert cart.get_total() == 3.0


def test_zero_price_item_is_valid(cart):
    cart.add_item("FREE", "Sample", 0.0, 3)
    assert cart.get_total() == 0.0


def test_carts_do_not_share_state():
    first = ShoppingCart()
    second = ShoppingCart()
    first.add_item("A1", "Apple", 1.5, 2)
    assert first.get_total() == 3.0
    assert second.get_total() == 0.0


def test_default_quantity_is_one(cart):
    cart.add_item("A1", "Apple", 1.5)
    assert cart.get_total() == 1.5


def test_removing_exact_quantity_removes_the_entire_line_item(cart):
    cart.add_item("A1", "Apple", 1.5, 3)
    cart.remove_item("A1", 3)
    assert cart.get_total() == 0.0


def test_invalid_addition_for_existing_item_preserves_current_total(cart):
    cart.add_item("A1", "Apple", 1.5, 2)
    with pytest.raises(ValueError):
        cart.add_item("A1", "Apple", -1.0, 3)
    assert cart.get_total() == 3.0


def test_multiple_line_items_can_be_removed_independently(cart):
    cart.add_item("A1", "Apple", 1.5, 2)
    cart.add_item("B2", "Banana", 0.75, 4)
    cart.remove_item("B2", 3)
    assert cart.get_total() == 3.75
