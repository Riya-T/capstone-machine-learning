"""Shopping cart: item quantities, prices and the cart total.

Planted bug (after c_discounts and c_undo): undo works, but add_item no
longer rejects a bad quantity, breaking the initial spec. Never shown to the
writer or the editor; validate-tasks checks that the tests catch it.

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
        self.discount_rate = 0.0

    def _save_state(self):
        self.history.append({item_id: dict(item) for item_id, item in self.items.items()})

    def add_item(self, item_id: str, name: str, price: float, quantity: int = 1):
        if price < 0:
            raise ValueError("Price must be non-negative")
        self._save_state()
        if item_id in self.items:
            self.items[item_id]["quantity"] += quantity
        else:
            self.items[item_id] = {"name": name, "price": price, "quantity": quantity}

    def apply_discount_code(self, code: str):
        if code != "SAVE10":
            raise ValueError("Invalid coupon")
        self.discount_rate = 0.10

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
        subtotal = sum(item["price"] * item["quantity"] for item in self.items.values())
        return subtotal * (1.0 - self.discount_rate)
