"""Pantry inventory with a minimum stock per item, a shopping list, and a
current day so batches past their use-by day are expired.

Planted bug (after c_shopping_list and c_expired): expiry was added
correctly, but set_minimum no longer checks the minimum it is given.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from pantry import Pantry
    pantry = Pantry()
    pantry.add_item("milk", 2, use_by=3)
    pantry.set_minimum("milk", 6)
    pantry.set_day(4)
    pantry.get_usable_quantity("milk")  # 0
"""


def check_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"quantity must be a positive int, got {quantity!r}")


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day < 0:
        raise ValueError(f"day must be an int >= 0, got {day!r}")


class Pantry:
    def __init__(self):
        # name -> list of [use_by, left], in the order added; used-up
        # batches are kept, and only discard_expired removes batches
        self._batches = {}
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
        wanted = quantity
        for batch in self._batches[name]:  # first in, first out
            if wanted == 0:
                break
            if self._is_expired(batch):
                continue
            taken = min(batch[1], wanted)
            batch[1] -= taken
            wanted -= taken

    def get_quantity(self, name):
        self._require(name)
        return sum(left for _, left in self._batches[name])

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
