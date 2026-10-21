"""Parking garage: vehicles parked on several levels, and how long each stayed.

Planted bug (initial version): a plate that is already parked may enter
again and takes a second spot. The public checks never try one, so only
the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from garage import Garage
    garage = Garage()
    garage.add_level("P1", 20)
    garage.enter("ABC-123", 60)
    garage.leave("ABC-123", 150)  # -> 90
"""


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


class Garage:
    def __init__(self):
        self._spots = {}  # level id -> number of spots, in the order added
        self._parked = {}  # level id -> plates on it, in entry order
        self._tickets = {}  # plate -> (level id, entry minute)

    def add_level(self, level_id, spots):
        check_name(level_id, "level_id")
        if isinstance(spots, bool) or not isinstance(spots, int) or spots <= 0:
            raise ValueError(f"spots must be a positive int, got {spots!r}")
        if level_id in self._spots:
            raise GarageError(f"level {level_id!r} was already added")
        self._spots[level_id] = spots
        self._parked[level_id] = []

    def enter(self, plate, minute):
        check_name(plate, "plate")
        check_minute(minute)
        level_id = self._find_level()
        self._parked[level_id].append(plate)
        self._tickets[plate] = (level_id, minute)
        return level_id

    def leave(self, plate, minute):
        self._require_parked(plate)
        level_id, entered = self._tickets[plate]
        check_minute(minute, lowest=entered)
        del self._tickets[plate]
        self._parked[level_id].remove(plate)
        return minute - entered

    def get_level(self, plate):
        self._require_parked(plate)
        return self._tickets[plate][0]

    def get_free_spots(self, level_id):
        self._require_level(level_id)
        return self._spots[level_id] - len(self._parked[level_id])

    def get_vehicles(self, level_id):
        self._require_level(level_id)
        return list(self._parked[level_id])

    def get_levels(self):
        return list(self._spots)

    def _find_level(self):
        for level_id in self._spots:
            if self.get_free_spots(level_id) > 0:
                return level_id
        raise GarageFull("no level has a free spot")

    def _require_level(self, level_id):
        # Non-str ids are never stored, so they count as "not added" too.
        if not isinstance(level_id, str) or level_id not in self._spots:
            raise KeyError(level_id)

    def _require_parked(self, plate):
        if not isinstance(plate, str) or plate not in self._tickets:
            raise KeyError(plate)
