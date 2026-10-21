"""Shopping cart: item quantities, prices and the cart total.

Planted bug (initial version): add_item and remove_item validate nothing:
negative prices and bad quantities are accepted, re-adding an item replaces
its price, and removing everything leaves a line with quantity 0 or less.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

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
        # BUG: Allows negative quantities to reduce total without checks
        self.items[item_id] = {"name": name, "price": price, "quantity": self.items.get(item_id, {}).get("quantity", 0) + quantity}

    def remove_item(self, item_id: str, quantity: int = 1):
        if item_id in self.items:
            self.items[item_id]["quantity"] -= quantity

    def get_total(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self.items.values())