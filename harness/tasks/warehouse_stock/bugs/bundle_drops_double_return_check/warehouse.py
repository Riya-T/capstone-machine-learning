"""Warehouse stock with returnable orders and all-or-nothing bundles of
several products.

Planted bug (after c_returns and c_bundle): bundles work, but while the
order-taking code was pulled into a helper the check that an order can
only be returned once was lost, so returning twice puts the units back
twice. Never shown to the writer or the editor; validate-tasks checks that
the tests catch it.

Usage:
    from warehouse import Warehouse
    wh = Warehouse()
    wh.add_product("bolt")
    wh.add_product("nut")
    wh.receive("bolt", 100)
    wh.receive("nut", 100)
    ids = wh.place_bundle([("bolt", 10), ("nut", 20)])
    wh.return_order(ids[0])
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
        self._require_stock(sku, quantity)
        return self._take(sku, quantity)

    def place_bundle(self, lines):
        lines = list(lines)
        if not lines:
            raise ValueError("a bundle needs at least one line")
        for sku, _ in lines:
            self._require_product(sku)
        for _, quantity in lines:
            check_quantity(quantity)
        skus = [sku for sku, _ in lines]
        if len(set(skus)) != len(skus):
            raise ValueError("a sku may appear only once per bundle")
        for sku, quantity in lines:
            self._require_stock(sku, quantity)
        return [self._take(sku, quantity) for sku, quantity in lines]

    def return_order(self, order_id):
        sku, quantity = self.get_order(order_id)
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

    def _take(self, sku, quantity):
        # Called only after every check passed.
        self._stock[sku] -= quantity
        self._history[sku].append(("ordered", quantity))
        order_id = len(self._orders) + 1
        self._orders[order_id] = (sku, quantity)
        return order_id

    def _require_product(self, sku):
        # Non-str skus are never stored, so they count as "not a product" too.
        if not isinstance(sku, str) or sku not in self._stock:
            raise KeyError(sku)

    def _require_stock(self, sku, quantity):
        if quantity > self._stock[sku]:
            raise OutOfStock(f"only {self._stock[sku]} of {sku!r} in stock")
