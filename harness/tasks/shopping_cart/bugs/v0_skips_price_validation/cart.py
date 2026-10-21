"""Shopping cart: item quantities, prices and the cart total.

Planted bug (initial version): add_item accepts a negative price, re-adding
an item replaces its quantity, and remove_item validates nothing and never
drops a line. Never shown to the writer or the editor; validate-tasks checks
that the tests catch it.

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
        # BUG: Ignores negative prices
        self.items[item_id] = {"name": name, "price": price, "quantity": quantity}

    def remove_item(self, item_id: str, quantity: int = 1):
        if item_id in self.items:
            self.items[item_id]["quantity"] -= quantity

    def get_total(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self.items.values())