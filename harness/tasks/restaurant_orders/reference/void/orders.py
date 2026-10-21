"""Restaurant orders with voiding of a table's most recent order.

Correct solution for restaurant_orders after c_void.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from orders import Restaurant
    rest = Restaurant()
    rest.add_dish("soup", 650)
    rest.open_table("t1")
    rest.order("t1", "soup", 2)
    rest.void_last("t1")
"""


class RestaurantError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


class Sitting:
    """One table from opening to closing: its live order lines and voided ones."""

    def __init__(self):
        self.lines = []  # (dish, quantity) per order call still standing
        self.voided = []  # (dish, quantity) per voided call, in voiding order


class Restaurant:
    def __init__(self):
        self._menu = {}  # dish name -> price in cents
        self._tables = {}  # open table -> Sitting, in opening order

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
        self._tables[table] = Sitting()

    def order(self, table, dish, quantity):
        sitting = self._require(table)
        if not isinstance(dish, str) or dish not in self._menu:
            raise KeyError(dish)
        check_positive(quantity, "quantity")
        sitting.lines.append((dish, quantity))

    def void_last(self, table):
        sitting = self._require(table)
        if not sitting.lines:
            raise RestaurantError(f"table {table!r} has nothing to void")
        line = sitting.lines.pop()
        sitting.voided.append(line)
        return line

    def get_order(self, table):
        totals = {}
        for dish, quantity in self._require(table).lines:
            totals[dish] = totals.get(dish, 0) + quantity
        return list(totals.items())

    def get_voided(self, table):
        return list(self._require(table).voided)

    def get_bill(self, table):
        return sum(quantity * self._menu[dish] for dish, quantity in self._require(table).lines)

    def close_table(self, table):
        self._require(table)
        del self._tables[table]

    def get_open_tables(self):
        return list(self._tables)

    def _require(self, table):
        # Non-str tables are never stored, so they count as "not open" too.
        if not isinstance(table, str) or table not in self._tables:
            raise KeyError(table)
        return self._tables[table]
