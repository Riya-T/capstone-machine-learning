"""Pantry inventory with a minimum stock per item and a shopping list of
what is missing.

Correct solution for pantry_inventory after c_shopping_list.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from pantry import Pantry
    pantry = Pantry()
    pantry.add_item("milk", 2, use_by=3)
    pantry.set_minimum("milk", 6)
    pantry.get_shopping_list()  # [("milk", 4)]
"""


def check_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"quantity must be a positive int, got {quantity!r}")


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day < 0:
        raise ValueError(f"day must be an int >= 0, got {day!r}")


class Pantry:
    def __init__(self):
        # name -> list of [use_by, left], in the order added; batches are never removed
        self._batches = {}
        self._minimums = {}  # name -> minimum stock; missing means 0

    def add_item(self, name, quantity, use_by):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        check_quantity(quantity)
        check_day(use_by)
        self._batches.setdefault(name, []).append([use_by, quantity])

    def use_item(self, name, quantity):
        self._require(name)
        check_quantity(quantity)
        wanted = quantity
        for batch in self._batches[name]:  # first in, first out
            if wanted == 0:
                break
            taken = min(batch[1], wanted)
            batch[1] -= taken
            wanted -= taken

    def get_quantity(self, name):
        self._require(name)
        return sum(left for _, left in self._batches[name])

    def get_batches(self, name):
        self._require(name)
        return [(use_by, left) for use_by, left in self._batches[name]]

    def get_expiring_by(self, day):
        check_day(day)
        expiring = []
        for name, batches in self._batches.items():
            units = sum(left for use_by, left in batches if use_by <= day)
            if units > 0:
                expiring.append((name, units))
        return expiring

    def get_items(self):
        return list(self._batches)

    def set_minimum(self, name, minimum):
        self._require(name)
        check_day(minimum)  # same rule: an int that is 0 or more
        self._minimums[name] = minimum

    def get_minimum(self, name):
        self._require(name)
        return self._minimums.get(name, 0)

    def get_shopping_list(self, day=None):
        if day is not None:
            check_day(day)
        shopping = []
        for name, batches in self._batches.items():
            stock = sum(left for use_by, left in batches if day is None or use_by >= day)
            missing = self.get_minimum(name) - stock
            if missing > 0:
                shopping.append((name, missing))
        return shopping

    def _require(self, name):
        # Non-str names are never stored, so they count as "not an item" too.
        if not isinstance(name, str) or name not in self._batches:
            raise KeyError(name)
