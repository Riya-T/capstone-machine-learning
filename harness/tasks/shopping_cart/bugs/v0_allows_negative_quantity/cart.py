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