"""Shopping cart: item quantities, prices and the cart total.

Correct solution for shopping_cart after c_undo alone. No sequence in
task.yaml reaches this set of changes, so the harness does not load it.
Never shown to the writer or the editor.

Usage:
    from cart import ShoppingCart
    cart = ShoppingCart()
    cart.add_item("apple", "Apple", 0.5, quantity=3)
    cart.get_total()
"""

class ShoppingCart:
    def __init__(self):
        self.items = {}
        self.history = []

    def _save_state(self):
        self.history.append({item_id: dict(item) for item_id, item in self.items.items()})

    def add_item(self, item_id: str, name: str, price: float, quantity: int = 1):
        if price < 0:
            raise ValueError("Price must be non-negative")
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")
        self._save_state()
        if item_id in self.items:
            self.items[item_id]["quantity"] += quantity
        else:
            self.items[item_id] = {"name": name, "price": price, "quantity": quantity}

    def remove_item(self, item_id: str, quantity: int = 1):
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer")
        if item_id not in self.items:
            return
        self._save_state()
        remaining = self.items[item_id]["quantity"] - quantity
        if remaining <= 0:
            del self.items[item_id]
        else:
            self.items[item_id]["quantity"] = remaining

    def undo(self):
        if not self.history:
            return False
        self.items = self.history.pop()
        return True

    def get_total(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self.items.values())
