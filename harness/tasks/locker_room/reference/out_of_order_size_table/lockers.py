"""Locker room with an adjustable table of sizes and fees, an optional fee
for each locker, and lockers that can be taken out of service.

Correct solution for locker_room after c_size_table and c_out_of_order.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from lockers import LockerRoom
    room = LockerRoom()
    room.add_locker("A1", "small")
    room.add_locker("A2", "small")
    room.set_out_of_order("A1")
    room.store("umbrella", "small")  # "A2"
"""

DEFAULT_SIZE_TABLE = {"small": 200, "medium": 300, "large": 500}  # smallest first


class LockerError(Exception):
    pass


class NoLockerFree(LockerError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_fee(fee):
    if isinstance(fee, bool) or not isinstance(fee, int) or fee < 0:
        raise ValueError(f"fee must be an int >= 0, got {fee!r}")


def check_size_table(table):
    if not isinstance(table, dict) or not table:
        raise ValueError("size_table must be a non-empty dict")
    for name, fee in table.items():
        check_id(name, "size name")
        check_fee(fee)


class LockerRoom:
    def __init__(self, size_table=None):
        if size_table is None:
            size_table = DEFAULT_SIZE_TABLE
        check_size_table(size_table)
        self._table = dict(size_table)  # size name -> fee, smallest first
        self._order = list(self._table)  # size names, smallest first
        self._sizes = {}  # locker id -> size, in the order added
        self._fees = {}  # locker id -> fee that locker charges
        self._contents = {}  # locker id -> item id, for lockers in use
        self._items = {}  # item id -> locker id
        self._broken = set()  # ids of lockers that are out of order
        self._takings = 0

    def add_locker(self, locker_id, size, fee=None):
        check_id(locker_id, "locker_id")
        self._check_size(size)
        if fee is None:
            fee = self._table[size]
        check_fee(fee)
        if locker_id in self._sizes:
            raise LockerError(f"locker {locker_id!r} was already added")
        self._sizes[locker_id] = size
        self._fees[locker_id] = fee

    def store(self, item_id, size):
        check_id(item_id, "item_id")
        self._check_size(size)
        if item_id in self._items:
            raise LockerError(f"item {item_id!r} is already in a locker")
        locker_id = self._choose(size)
        self._contents[locker_id] = item_id
        self._items[item_id] = locker_id
        self._takings += self._fees[locker_id]
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
        return [locker_id for locker_id in self._sizes if self._is_free(locker_id)]

    def get_takings(self):
        return self._takings

    def get_sizes(self):
        return list(self._order)

    def get_fee(self, locker_id):
        self._require_locker(locker_id)
        return self._fees[locker_id]

    def set_out_of_order(self, locker_id):
        self._require_locker(locker_id)
        self._broken.add(locker_id)

    def set_in_service(self, locker_id):
        self._require_locker(locker_id)
        self._broken.discard(locker_id)

    def is_out_of_order(self, locker_id):
        self._require_locker(locker_id)
        return locker_id in self._broken

    def _require_locker(self, locker_id):
        if not isinstance(locker_id, str) or locker_id not in self._sizes:
            raise KeyError(locker_id)

    def _is_free(self, locker_id):
        return locker_id not in self._contents and locker_id not in self._broken

    def _check_size(self, size):
        if not isinstance(size, str) or size not in self._table:
            raise ValueError(f"unknown size {size!r}")

    def _choose(self, size):
        free = self.get_free_lockers()
        for locker_size in self._order[self._order.index(size):]:
            for locker_id in free:
                if self._sizes[locker_id] == locker_size:
                    return locker_id
        raise NoLockerFree(f"no free locker fits a {size} item")
