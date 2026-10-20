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