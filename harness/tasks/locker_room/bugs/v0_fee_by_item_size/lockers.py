"""Locker room: items go into the smallest free locker that fits them, a fee
is taken per locker size, and items are handed back later.

Planted bug (initial version): store charges the fee of the item's size
instead of the chosen locker's size. The public checks only put items into
lockers of their own size, so only the hidden initial tests catch it.
Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from lockers import LockerRoom
    room = LockerRoom()
    room.add_locker("A1", "small")
    room.store("umbrella", "small")  # "A1"
    room.retrieve("umbrella")
"""

SIZES = ["small", "medium", "large"]  # smallest first
FEES = {"small": 200, "medium": 300, "large": 500}  # cents per stored item


class LockerError(Exception):
    pass


class NoLockerFree(LockerError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_size(size):
    if size not in SIZES:
        raise ValueError(f"unknown size {size!r}")


class LockerRoom:
    def __init__(self):
        self._sizes = {}  # locker id -> size, in the order added
        self._contents = {}  # locker id -> item id, for lockers in use
        self._items = {}  # item id -> locker id
        self._takings = 0

    def add_locker(self, locker_id, size):
        check_id(locker_id, "locker_id")
        check_size(size)
        if locker_id in self._sizes:
            raise LockerError(f"locker {locker_id!r} was already added")
        self._sizes[locker_id] = size

    def store(self, item_id, size):
        check_id(item_id, "item_id")
        check_size(size)
        if item_id in self._items:
            raise LockerError(f"item {item_id!r} is already in a locker")
        locker_id = self._choose(size)
        self._contents[locker_id] = item_id
        self._items[item_id] = locker_id
        self._takings += FEES[size]
        return locker_id

    def retrieve(self, item_id):
        locker_id = self.get_locker(item_id)
        del self._items[item_id]
        del self._contents[locker_id]
        return locker_id

    def get_locker(self, item_id):
        # Non-str ids are never stored, so they count as "not in a locker".
        if not isinstance(item_id, str) or item_id not in self._items:
            raise KeyError(item_id)
        return self._items[item_id]

    def get_free_lockers(self):
        return [locker_id for locker_id in self._sizes if locker_id not in self._contents]

    def get_takings(self):
        return self._takings

    def _choose(self, size):
        free = self.get_free_lockers()
        for locker_size in SIZES[SIZES.index(size):]:
            for locker_id in free:
                if self._sizes[locker_id] == locker_size:
                    return locker_id
        raise NoLockerFree(f"no free locker fits a {size} item")
