"""Parking garage with reserved spots and vehicle and level sizes.

Planted bug (after c_reserve and c_sizes): sizes were added correctly, but
`enter` now always searches for a fitting level and ignores the plate's
reservation, which is left in place.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from garage import Garage
    garage = Garage()
    garage.add_level("P1", 20, max_size="small")
    garage.reserve("P1", "ABC-123")
    garage.enter("ABC-123", 60, size="small")  # -> "P1"
"""

SIZES = ("small", "medium", "large")  # smallest to largest


class GarageError(Exception):
    pass


class GarageFull(GarageError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_minute(minute, lowest=0):
    if isinstance(minute, bool) or not isinstance(minute, int) or minute < lowest:
        raise ValueError(f"minute must be an int >= {lowest}, got {minute!r}")


def check_size(size):
    if size not in SIZES:
        raise ValueError(f"size must be one of {SIZES}, got {size!r}")


def fits(size, max_size):
    return SIZES.index(size) <= SIZES.index(max_size)


class Garage:
    def __init__(self):
        self._spots = {}  # level id -> number of spots, in the order added
        self._max_size = {}  # level id -> largest size accepted
        self._parked = {}  # level id -> plates on it, in entry order
        self._tickets = {}  # plate -> (level id, entry minute, size)
        self._reservations = {}  # plate -> level id, in reservation order

    def add_level(self, level_id, spots, max_size="large"):
        check_name(level_id, "level_id")
        if isinstance(spots, bool) or not isinstance(spots, int) or spots <= 0:
            raise ValueError(f"spots must be a positive int, got {spots!r}")
        check_size(max_size)
        if level_id in self._spots:
            raise GarageError(f"level {level_id!r} was already added")
        self._spots[level_id] = spots
        self._max_size[level_id] = max_size
        self._parked[level_id] = []

    def enter(self, plate, minute, size="medium"):
        check_name(plate, "plate")
        check_minute(minute)
        check_size(size)
        if plate in self._tickets:
            raise GarageError(f"{plate!r} is already parked")
        level_id = self._find_level(size)
        self._parked[level_id].append(plate)
        self._tickets[plate] = (level_id, minute, size)
        return level_id

    def leave(self, plate, minute):
        self._require_parked(plate)
        level_id, entered, _ = self._tickets[plate]
        check_minute(minute, lowest=entered)
        del self._tickets[plate]
        self._parked[level_id].remove(plate)
        return minute - entered

    def reserve(self, level_id, plate):
        self._require_level(level_id)
        check_name(plate, "plate")
        if plate in self._tickets or plate in self._reservations:
            raise GarageError(f"{plate!r} is already parked or reserved")
        if self.get_free_spots(level_id) == 0:
            raise GarageFull(f"level {level_id!r} has no free spot")
        self._reservations[plate] = level_id

    def cancel_reservation(self, plate):
        if not isinstance(plate, str) or plate not in self._reservations:
            raise KeyError(plate)
        del self._reservations[plate]

    def has_reservation(self, plate):
        return isinstance(plate, str) and plate in self._reservations

    def get_reserved(self, level_id):
        self._require_level(level_id)
        return [plate for plate, lvl in self._reservations.items() if lvl == level_id]

    def get_level(self, plate):
        self._require_parked(plate)
        return self._tickets[plate][0]

    def get_size(self, plate):
        self._require_parked(plate)
        return self._tickets[plate][2]

    def get_free_spots(self, level_id):
        self._require_level(level_id)
        taken = len(self._parked[level_id]) + len(self.get_reserved(level_id))
        return self._spots[level_id] - taken

    def get_max_size(self, level_id):
        self._require_level(level_id)
        return self._max_size[level_id]

    def get_vehicles(self, level_id):
        self._require_level(level_id)
        return list(self._parked[level_id])

    def get_levels(self):
        return list(self._spots)

    def _find_level(self, size):
        for level_id in self._spots:
            if fits(size, self._max_size[level_id]) and self.get_free_spots(level_id) > 0:
                return level_id
        raise GarageFull(f"no level with a free spot takes a {size} vehicle")

    def _require_level(self, level_id):
        # Non-str ids are never stored, so they count as "not added" too.
        if not isinstance(level_id, str) or level_id not in self._spots:
            raise KeyError(level_id)

    def _require_parked(self, plate):
        if not isinstance(plate, str) or plate not in self._tickets:
            raise KeyError(plate)
