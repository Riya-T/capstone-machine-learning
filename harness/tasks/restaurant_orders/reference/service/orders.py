"""Restaurant orders with a service charge on bills and the day's takings.

Correct solution for restaurant_orders after c_service.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from orders import Restaurant
    rest = Restaurant(service_percent=10)
    rest.add_dish("soup", 650)
    rest.open_table("t1")
    rest.order("t1", "soup", 2)
    rest.get_bill("t1")
"""


class RestaurantError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_non_negative(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{what} must be an int >= 0, got {value!r}")


class Restaurant:
    def __init__(self, service_percent=0):
        check_non_negative(service_percent, "service percent")
        self._service_percent = service_percent
        self._menu = {}  # dish name -> price in cents
        self._tables = {}  # open table -> list of (dish, quantity) lines, in opening order
        self._closed_bills = []  # the bill of every closed sitting, in closing order

    def add_dish(self, name, price):
        check_name(name, "dish name")
        check_positive(price, "price")
        if name in self._menu:
            raise RestaurantError(f"dish {name!r} is already on the menu")
        self._menu[name] = price

    def open_table(self, table):
        check_name(table, "table")
        if table in self._tables:
            raise RestaurantError(f"table {table!r} is already open")
        self._tables[table] = []

    def order(self, table, dish, quantity):
        lines = self._require(table)
        if not isinstance(dish, str) or dish not in self._menu:
            raise KeyError(dish)
        check_positive(quantity, "quantity")
        lines.append((dish, quantity))

    def get_order(self, table):
        totals = {}
        for dish, quantity in self._require(table):
            totals[dish] = totals.get(dish, 0) + quantity
        return list(totals.items())

    def get_subtotal(self, table):
        return sum(quantity * self._menu[dish] for dish, quantity in self._require(table))

    def get_service_charge(self, table):
        return self.get_subtotal(table) * self._service_percent // 100

    def get_bill(self, table):
        return self.get_subtotal(table) + self.get_service_charge(table)

    def get_takings(self):
        return sum(self._closed_bills)

    def close_table(self, table):
        self._closed_bills.append(self.get_bill(table))
        del self._tables[table]

    def get_open_tables(self):
        return list(self._tables)

    def _require(self, table):
        # Non-str tables are never stored, so they count as "not open" too.
        if not isinstance(table, str) or table not in self._tables:
            raise KeyError(table)
        return self._tables[table]
