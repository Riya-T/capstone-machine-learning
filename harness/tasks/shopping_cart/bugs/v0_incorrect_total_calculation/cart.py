"""Shopping cart: item quantities, prices and the cart total.

Planted bug (initial version): get_total adds up prices without multiplying
by quantity; add_item and remove_item also skip most validation. Never shown
to the writer or the editor; validate-tasks checks that the tests catch it.

Usage:
    from cart import ShoppingCart
    cart = ShoppingCart()
    cart.add_item("apple", "Apple", 0.5, quantity=3)
    cart.get_total()
"""

class ShoppingCart:
    def __init__(self):
        self.items = {}

    def add_item(self, item_id: str, name: str, price: float, quantity: int = 1):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        self.items[item_id] = {"name": name, "price": price, "quantity": quantity}

    def remove_item(self, item_id: str, quantity: int = 1):
        if item_id in self.items:
            self.items[item_id]["quantity"] -= quantity

    def get_total(self) -> float:
        # BUG: Multiplies totals incorrectly or misses values
        return sum(item["price"] for item in self.items.values())