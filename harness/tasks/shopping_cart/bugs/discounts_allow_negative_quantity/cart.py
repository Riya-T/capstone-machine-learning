class ShoppingCart:
    def __init__(self, stock_inventory: dict = None):
        self.items = {}
        self.stock_inventory = dict(stock_inventory or {})
        self.discount_rate = 0.0

    def add_item(self, item_id: str, name: str, price: float, quantity: int = 1):
        if price < 0:
            raise ValueError("Price must be non-negative")
        current_quantity = self.items.get(item_id, {}).get("quantity", 0)
        resulting_quantity = current_quantity + quantity
        if item_id in self.stock_inventory and resulting_quantity > self.stock_inventory[item_id]:
            raise ValueError("Requested quantity exceeds stock")
        if item_id in self.items:
            self.items[item_id]["quantity"] = resulting_quantity
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
        remaining = self.items[item_id]["quantity"] - quantity
        if remaining <= 0:
            del self.items[item_id]
        else:
            self.items[item_id]["quantity"] = remaining

    def get_total(self) -> float:
        subtotal = sum(item["price"] * item["quantity"] for item in self.items.values())
        return subtotal * (1.0 - self.discount_rate)
