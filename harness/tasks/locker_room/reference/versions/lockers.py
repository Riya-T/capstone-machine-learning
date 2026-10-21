"""Locker room with a version number per locker, moves between lockers and
checks that stop a desk from acting on a locker that changed meanwhile.

Correct solution for locker_room after c_versions.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from lockers import LockerRoom
    room = LockerRoom()
    room.add_locker("A1", "small")
    room.add_locker("B1", "large")
    room.store("umbrella", "small")  # "A1"; A1 is now at version 2
    room.move("umbrella", "B1", expected_version=1)
"""

SIZES = ["small", "medium", "large"]  # smallest first
FEES = {"small": 200, "medium": 300, "large": 500}  # cents per stored item


class LockerError(Exception):
    pass


class NoLockerFree(LockerError):
    pass


class VersionConflict(LockerError):
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
        self._versions = {}  # locker id -> version number
        self._contents = {}  # locker id -> item id, for lockers in use
        self._items = {}  # item id -> (locker id, item size)
        self._takings = 0

    def add_locker(self, locker_id, size):
        check_id(locker_id, "locker_id")
        check_size(size)
        if locker_id in self._sizes:
            raise LockerError(f"locker {locker_id!r} was already added")
        self._sizes[locker_id] = size
        self._versions[locker_id] = 1

    def store(self, item_id, size):
        check_id(item_id, "item_id")
        check_size(size)
        if item_id in self._items:
            raise LockerError(f"item {item_id!r} is already in a locker")
        locker_id = self._choose(size)
        self._put(item_id, size, locker_id)
        self._takings += FEES[self._sizes[locker_id]]
        return locker_id

    def retrieve(self, item_id, expected_version=None):
        locker_id = self.get_locker(item_id)
        self._check_version(locker_id, expected_version)
        self._take(item_id, locker_id)
        return locker_id

    def move(self, item_id, locker_id, expected_version=None):
        old_locker = self.get_locker(item_id)
        self._require_locker(locker_id)
        self._check_version(locker_id, expected_version)
        if locker_id in self._contents:
            raise LockerError(f"locker {locker_id!r} is not empty")
        size = self._items[item_id][1]
        if not self._fits(size, locker_id):
            raise LockerError(f"locker {locker_id!r} is too small for a {size} item")
        self._take(item_id, old_locker)
        self._put(item_id, size, locker_id)

    def get_locker(self, item_id):
        # Non-str ids are never stored, so they count as "not in a locker".
        if not isinstance(item_id, str) or item_id not in self._items:
            raise KeyError(item_id)
        return self._items[item_id][0]

    def get_free_lockers(self):
        return [locker_id for locker_id in self._sizes if locker_id not in self._contents]

    def get_takings(self):
        return self._takings

    def get_version(self, locker_id):
        self._require_locker(locker_id)
        return self._versions[locker_id]

    def _put(self, item_id, size, locker_id):
        self._contents[locker_id] = item_id
        self._items[item_id] = (locker_id, size)
        self._versions[locker_id] += 1

    def _take(self, item_id, locker_id):
        del self._items[item_id]
        del self._contents[locker_id]
        self._versions[locker_id] += 1

    def _require_locker(self, locker_id):
        if not isinstance(locker_id, str) or locker_id not in self._sizes:
            raise KeyError(locker_id)

    def _check_version(self, locker_id, expected_version):
        current = self._versions[locker_id]
        if expected_version is not None and expected_version != current:
            raise VersionConflict(
                f"locker {locker_id!r} is at version {current}, not {expected_version!r}"
            )

    def _fits(self, item_size, locker_id):
        return SIZES.index(self._sizes[locker_id]) >= SIZES.index(item_size)

    def _choose(self, size):
        free = self.get_free_lockers()
        for locker_size in SIZES[SIZES.index(size):]:
            for locker_id in free:
                if self._sizes[locker_id] == locker_size:
                    return locker_id
        raise NoLockerFree(f"no free locker fits a {size} item")
