"""Seating chart with undo.

Correct solution for seating_chart after c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from seating import SeatingChart
    chart = SeatingChart()
    chart.add_table("rose")
    chart.seat("Ann", "rose")
    chart.undo()  # rose is empty again
"""


class SeatingError(Exception):
    pass


def check_name(name, what):
    if not isinstance(name, str) or not name:
        raise ValueError(f"{what} must be a non-empty str, got {name!r}")


class SeatingChart:
    def __init__(self):
        # table name -> guests in seating order, in the order the tables
        # were added; plus each seated guest's table, for quick lookups.
        self._tables = {}
        self._table_of = {}
        self._undo_stack = []  # copies of the state as it was before each call

    def add_table(self, name):
        check_name(name, "table name")
        if name in self._tables:
            raise SeatingError(f"table name {name!r} is already used")
        self._save()
        self._tables[name] = []

    def seat(self, guest, table):
        check_name(guest, "guest")
        self._require_table(table)
        if guest in self._table_of:
            raise SeatingError(f"{guest!r} is already seated")
        self._save()
        self._tables[table].append(guest)
        self._table_of[guest] = table

    def unseat(self, guest):
        self._require_guest(guest)
        self._save()
        table = self._table_of.pop(guest)
        self._tables[table].remove(guest)

    def move_guest(self, guest, table):
        self._require_guest(guest)
        self._require_table(table)
        old = self._table_of[guest]
        if old == table:
            raise ValueError(f"{guest!r} already sits at {table!r}")
        self._save()
        self._tables[old].remove(guest)
        self._tables[table].append(guest)
        self._table_of[guest] = table

    def merge_tables(self, table, into_table):
        self._require_table(table)
        self._require_table(into_table)
        if table == into_table:
            raise ValueError("cannot merge a table into itself")
        self._save()
        guests = self._tables.pop(table)
        self._tables[into_table].extend(guests)
        for guest in guests:
            self._table_of[guest] = into_table
        return len(guests)

    def clear_table(self, table):
        self._require_table(table)
        self._save()
        guests = self._tables.pop(table)
        for guest in guests:
            del self._table_of[guest]
        return len(guests)

    def undo(self):
        if not self._undo_stack:
            raise SeatingError("nothing to undo")
        self._tables, self._table_of = self._undo_stack.pop()

    def get_guests(self, table):
        self._require_table(table)
        return list(self._tables[table])

    def get_tables(self):
        return list(self._tables)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        tables = {name: list(guests) for name, guests in self._tables.items()}
        self._undo_stack.append((tables, dict(self._table_of)))

    def _require_table(self, table):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(table, str) or table not in self._tables:
            raise KeyError(table)

    def _require_guest(self, guest):
        if not isinstance(guest, str) or guest not in self._table_of:
            raise KeyError(guest)
