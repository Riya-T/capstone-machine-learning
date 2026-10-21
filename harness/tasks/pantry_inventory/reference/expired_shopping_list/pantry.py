"""Pantry inventory with a minimum stock per item, a shopping list, and a
current day so batches past their use-by day are expired.

Correct solution for pantry_inventory after c_shopping_list and c_expired.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from pantry import Pantry
    pantry = Pantry()
    pantry.add_item("milk", 2, use_by=3)
    pantry.set_minimum("milk", 6)
    pantry.set_day(4)
    pantry.get_usable_quantity("milk")  # 0
"""


class PantryError(Exception):
    pass


def check_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"quantity must be a positive int, got {quantity!r}")


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day < 0:
        raise ValueError(f"day must be an int >= 0, got {day!r}")


class Pantry:
    def __init__(self):
        self._batches = {}  # name -> list of [use_by, quantity], in the order added
        self._minimums = {}  # name -> minimum stock; missing means 0
        self._day = 0

    def add_item(self, name, quantity, use_by):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        check_quantity(quantity)
        check_day(use_by)
        self._batches.setdefault(name, []).append([use_by, quantity])

    def use_item(self, name, quantity):
        self._require(name)
        check_quantity(quantity)
        usable = self.get_usable_quantity(name)
        if quantity > usable:
            raise PantryError(f"only {usable} of {name!r} can still be used")
        left = quantity
        for batch in self._earliest_first(name):
            if self._is_expired(batch):
                continue
            taken = min(batch[1], left)
            batch[1] -= taken
            left -= taken
            if left == 0:
                break
        self._batches[name] = [b for b in self._batches[name] if b[1] > 0]

    def get_quantity(self, name):
        self._require(name)
        return sum(quantity for _, quantity in self._batches[name])

    def get_usable_quantity(self, name):
        self._require(name)
        return sum(b[1] for b in self._batches[name] if not self._is_expired(b))

    def get_expired_quantity(self, name):
        self._require(name)
        return sum(b[1] for b in self._batches[name] if self._is_expired(b))

    def discard_expired(self, name):
        thrown = self.get_expired_quantity(name)
        self._batches[name] = [b for b in self._batches[name] if not self._is_expired(b)]
        return thrown

    def get_batches(self, name):
        self._require(name)
        return [(use_by, quantity) for use_by, quantity in self._earliest_first(name)]

    def get_expiring_by(self, day):
        check_day(day)
        return [
            name
            for name, batches in self._batches.items()
            if any(use_by <= day for use_by, _ in batches)
        ]

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
            stock = sum(q for use_by, q in batches if day is None or use_by >= day)
            missing = self.get_minimum(name) - stock
            if missing > 0:
                shopping.append((name, missing))
        return shopping

    def set_day(self, day):
        if isinstance(day, bool) or not isinstance(day, int) or day < self._day:
            raise ValueError(f"day must be an int >= {self._day}, got {day!r}")
        self._day = day

    def get_day(self):
        return self._day

    def _require(self, name):
        # Non-str names are never stored, so they count as "not an item" too.
        if not isinstance(name, str) or name not in self._batches:
            raise KeyError(name)

    def _is_expired(self, batch):
        return batch[0] < self._day

    def _earliest_first(self, name):
        # sorted() is stable, so batches with the same day keep their order.
        return sorted(self._batches[name], key=lambda b: b[0])
