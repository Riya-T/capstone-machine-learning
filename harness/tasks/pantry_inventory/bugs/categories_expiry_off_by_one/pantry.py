"""Pantry inventory with a current day, expired batches and item
categories.

Planted bug (after c_expired and c_categories): categories were added
correctly, but a batch now counts as expired on its use-by day itself
instead of only after it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from pantry import Pantry
    pantry = Pantry()
    pantry.add_item("milk", 2, use_by=3, category="dairy")
    pantry.set_day(4)
    pantry.get_items_in("dairy")  # ["milk"]
"""


DEFAULT_CATEGORY = "other"


def check_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"quantity must be a positive int, got {quantity!r}")


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day < 0:
        raise ValueError(f"day must be an int >= 0, got {day!r}")


def check_category(category):
    if not isinstance(category, str) or not category:
        raise ValueError(f"category must be a non-empty str, got {category!r}")


class Pantry:
    def __init__(self):
        # name -> list of [use_by, left], in the order added; used-up
        # batches are kept, and only discard_expired removes batches
        self._batches = {}
        self._categories = {}  # name -> category
        self._day = 0

    def add_item(self, name, quantity, use_by, category=None):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        check_quantity(quantity)
        check_day(use_by)
        if category is not None:
            check_category(category)
        self._batches.setdefault(name, []).append([use_by, quantity])
        # Only a new item takes the category; an existing one keeps its own.
        self._categories.setdefault(name, DEFAULT_CATEGORY if category is None else category)

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

    def set_day(self, day):
        if isinstance(day, bool) or not isinstance(day, int) or day < self._day:
            raise ValueError(f"day must be an int >= {self._day}, got {day!r}")
        self._day = day

    def get_day(self):
        return self._day

    def set_category(self, name, category):
        self._require(name)
        check_category(category)
        self._categories[name] = category

    def get_category(self, name):
        self._require(name)
        return self._categories[name]

    def get_categories(self):
        return sorted(set(self._categories.values()))

    def get_items_in(self, category):
        return sorted(name for name, cat in self._categories.items() if cat == category)

    def get_category_quantity(self, category):
        return sum(self.get_quantity(name) for name in self.get_items_in(category))

    def _require(self, name):
        # Non-str names are never stored, so they count as "not an item" too.
        if not isinstance(name, str) or name not in self._batches:
            raise KeyError(name)

    def _is_expired(self, batch):
        return batch[0] <= self._day
