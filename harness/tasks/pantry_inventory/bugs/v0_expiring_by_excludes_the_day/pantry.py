"""Pantry inventory: how much of each item is in the pantry, in batches that
each have a use-by day, used first in, first out. This one keeps used-up
batches listed with 0 units left; the spec also allows dropping them.

Planted bug (initial version): get_expiring_by leaves out batches whose
use-by day is the day asked about. The public checks never ask about the
exact day, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from pantry import Pantry
    pantry = Pantry()
    pantry.add_item("milk", 2, use_by=3)
    pantry.use_item("milk", 3)
    pantry.get_batches("milk")  # [(3, 0)]: only 2 were left
"""


def check_quantity(quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError(f"quantity must be a positive int, got {quantity!r}")


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day < 0:
        raise ValueError(f"day must be an int >= 0, got {day!r}")


class Pantry:
    def __init__(self):
        # name -> list of [use_by, left], in the order added; used-up batches are kept
        self._batches = {}

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
            units = sum(left for use_by, left in batches if use_by < day)
            if units > 0:
                expiring.append((name, units))
        return expiring

    def get_items(self):
        return list(self._batches)

    def _require(self, name):
        # Non-str names are never stored, so they count as "not an item" too.
        if not isinstance(name, str) or name not in self._batches:
            raise KeyError(name)
