"""Warehouse stock where an order can be returned to put its units back.

Correct solution for warehouse_stock after c_returns.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from warehouse import Warehouse
    wh = Warehouse()
    wh.add_product("bolt")
    wh.receive("bolt", 100)
    order = wh.place_order("bolt", 30)
    wh.return_order(order)
"""


class WarehouseError(Exception):
    pass


class OutOfStock(WarehouseError):
    pass


def check_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"quantity must be a positive int, got {quantity!r}")


class Warehouse:
    def __init__(self):
        self._stock = {}  # sku -> units on hand, in the order added
        self._history = {}  # sku -> list of (kind, quantity)
        self._orders = {}  # order id -> (sku, quantity)
        self._returned = set()  # ids of returned orders

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

    def return_order(self, order_id):
        sku, quantity = self.get_order(order_id)
        if order_id in self._returned:
            raise WarehouseError(f"order {order_id} was already returned")
        self._returned.add(order_id)
        self._stock[sku] += quantity
        self._history[sku].append(("returned", quantity))

    def is_returned(self, order_id):
        self.get_order(order_id)
        return order_id in self._returned

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

    def _require_product(self, sku):
        # Non-str skus are never stored, so they count as "not a product" too.
        if not isinstance(sku, str) or sku not in self._stock:
            raise KeyError(sku)
