"""Warehouse stock with ways to look through products and orders: low
stock, orders per product, and large orders.

Correct solution for warehouse_stock after c_lowstock.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from warehouse import Warehouse
    wh = Warehouse()
    wh.add_product("bolt")
    wh.receive("bolt", 5)
    wh.get_low_stock(10)
"""


class WarehouseError(Exception):
    pass


class OutOfStock(WarehouseError):
    pass


def check_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"quantity must be a positive int, got {quantity!r}")


def check_threshold(threshold):
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 0:
        raise ValueError(f"threshold must be an int >= 0, got {threshold!r}")


class Warehouse:
    def __init__(self):
        self._stock = {}  # sku -> units on hand, in the order added
        self._history = {}  # sku -> list of (kind, quantity)
        self._orders = {}  # order id -> (sku, quantity), in the order placed

    def add_product(self, sku):
        if not isinstance(sku, str) or not sku:
            raise ValueError("sku must be a non-empty str")
        if sku in self._stock:
            raise WarehouseError(f"product {sku!r} already exists")
        self._stock[sku] = 0
        self._history[sku] = []

    def receive(self, sku, quantity):
        self._require_product(sku)
        check_quantity(quantity)
        self._stock[sku] += quantity
        self._history[sku].append(("received", quantity))

    def place_order(self, sku, quantity):
        self._require_product(sku)
        check_quantity(quantity)
        if quantity > self._stock[sku]:
            raise OutOfStock(f"only {self._stock[sku]} of {sku!r} in stock")
        self._stock[sku] -= quantity
        self._history[sku].append(("ordered", quantity))
        order_id = len(self._orders) + 1
        self._orders[order_id] = (sku, quantity)
        return order_id

    def get_stock(self, sku):
        self._require_product(sku)
        return self._stock[sku]

    def get_order(self, order_id):
        if isinstance(order_id, bool) or order_id not in self._orders:
            raise KeyError(order_id)
        return self._orders[order_id]

    def get_history(self, sku):
        self._require_product(sku)
        return list(self._history[sku])

    def get_products(self):
        return list(self._stock)

    def get_low_stock(self, threshold):
        check_threshold(threshold)
        return [sku for sku, stock in self._stock.items() if stock < threshold]

    def get_orders(self, sku):
        self._require_product(sku)
        return [order_id for order_id, (s, _) in self._orders.items() if s == sku]

    def get_large_orders(self, min_quantity):
        check_quantity(min_quantity)
        return [order_id for order_id, (_, q) in self._orders.items() if q >= min_quantity]

    def _require_product(self, sku):
        # Non-str skus are never stored, so they count as "not a product" too.
        if not isinstance(sku, str) or sku not in self._stock:
            raise KeyError(sku)
