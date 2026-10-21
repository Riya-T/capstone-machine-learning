"""Restaurant orders with voiding of the most recent order and dishes grouped
into courses.

Planted bug (after c_void and c_courses): courses work, but while adding
them get_order and get_bill were rebuilt over every line the table ever
ordered, voided ones included, so voiding no longer changes them. The
course queries still skip voided lines, so the course tests pass.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from orders import Restaurant
    rest = Restaurant()
    rest.add_dish("soup", 650, course="starter")
    rest.open_table("t1")
    rest.order("t1", "soup", 2)
    rest.get_course_order("t1", "starter")
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
        self.all_lines = []  # (dish, quantity) per order call, voided or not
        self.lines = []  # (dish, quantity) per order call still standing
        self.voided = []  # (dish, quantity) per voided call, in voiding order


class Restaurant:
    def __init__(self):
        self._prices = {}  # dish name -> price in cents, in menu order
        self._courses = {}  # dish name -> course
        self._tables = {}  # open table -> Sitting, in opening order

    def add_dish(self, name, price, course="main"):
        check_name(name, "dish name")
        check_positive(price, "price")
        check_name(course, "course")
        if name in self._prices:
            raise RestaurantError(f"dish {name!r} is already on the menu")
        self._prices[name] = price
        self._courses[name] = course

    def open_table(self, table):
        check_name(table, "table")
        if table in self._tables:
            raise RestaurantError(f"table {table!r} is already open")
        self._tables[table] = Sitting()

    def order(self, table, dish, quantity):
        sitting = self._require(table)
        if not isinstance(dish, str) or dish not in self._prices:
            raise KeyError(dish)
        check_positive(quantity, "quantity")
        sitting.all_lines.append((dish, quantity))
        sitting.lines.append((dish, quantity))

    def void_last(self, table):
        sitting = self._require(table)
        if not sitting.lines:
            raise RestaurantError(f"table {table!r} has nothing to void")
        line = sitting.lines.pop()
        sitting.voided.append(line)
        return line

    def get_order(self, table):
        return self._totals(self._require(table).all_lines)

    def get_voided(self, table):
        return list(self._require(table).voided)

    def get_bill(self, table):
        return self._sum(self._require(table).all_lines)

    def get_courses(self):
        return list(dict.fromkeys(self._courses.values()))

    def get_course_order(self, table, course):
        return self._totals(self._course_lines(table, course))

    def get_course_bill(self, table, course):
        return self._sum(self._course_lines(table, course))

    def close_table(self, table):
        self._require(table)
        del self._tables[table]

    def get_open_tables(self):
        return list(self._tables)

    def _course_lines(self, table, course):
        lines = self._require(table).lines
        if course not in self.get_courses():
            raise KeyError(course)
        return [line for line in lines if self._courses[line[0]] == course]

    def _totals(self, lines):
        totals = {}
        for dish, quantity in lines:
            totals[dish] = totals.get(dish, 0) + quantity
        return list(totals.items())

    def _sum(self, lines):
        return sum(quantity * self._prices[dish] for dish, quantity in lines)

    def _require(self, table):
        # Non-str tables are never stored, so they count as "not open" too.
        if not isinstance(table, str) or table not in self._tables:
            raise KeyError(table)
        return self._tables[table]
