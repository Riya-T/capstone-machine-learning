"""Pantry inventory: how much of each item is in the pantry, in batches that
each have a use-by day.

Planted bug (initial version): using exactly everything that is left
raises PantryError. The public checks never empty an item, so only the
hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from pantry import Pantry
    pantry = Pantry()
    pantry.add_item("milk", 2, use_by=3)
    pantry.use_item("milk", 1)
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

    def add_item(self, name, quantity, use_by):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        check_quantity(quantity)
        check_day(use_by)
        self._batches.setdefault(name, []).append([use_by, quantity])

    def use_item(self, name, quantity):
        self._require(name)
        check_quantity(quantity)
        if quantity >= self.get_quantity(name):
            raise PantryError(f"only {self.get_quantity(name)} of {name!r} left")
        left = quantity
        for batch in self._earliest_first(name):
            taken = min(batch[1], left)
            batch[1] -= taken
            left -= taken
            if left == 0:
                break
        self._batches[name] = [b for b in self._batches[name] if b[1] > 0]

    def get_quantity(self, name):
        self._require(name)
        return sum(quantity for _, quantity in self._batches[name])

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

    def _require(self, name):
        # Non-str names are never stored, so they count as "not an item" too.
        if not isinstance(name, str) or name not in self._batches:
            raise KeyError(name)

    def _earliest_first(self, name):
        # sorted() is stable, so batches with the same day keep their order.
        return sorted(self._batches[name], key=lambda b: b[0])
