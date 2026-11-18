"""Bike docks with undo, station capacities and take orders.

Planted bug (after c_undo, c_capacity and c_take_order): take orders work,
but rebalance, rewritten to take the oldest or newest bikes, no longer
checks the capacity of to_station. Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from bikes import BikeNetwork
    net = BikeNetwork(take_order="newest")
    net.add_station("north")
    net.add_station("south")
    net.dock("north", "b1")
    net.dock("north", "b2")
    net.rebalance("north", "south", 1)  # moves b2
"""

import copy

TAKE_ORDERS = ("oldest", "newest")


class DockError(Exception):
    pass


class StationFull(DockError):
    pass


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_order(order):
    if not isinstance(order, str) or order not in TAKE_ORDERS:
        raise ValueError(f"take order must be 'oldest' or 'newest', got {order!r}")


class BikeNetwork:
    def __init__(self, take_order="oldest"):
        check_order(take_order)
        self._default_order = take_order
        # station name -> list of bikes in the order they arrived; the dict
        # keeps the stations in the order they were added.
        self._stations = {}
        self._where = {}  # bike -> name of the station it is docked at
        self._capacity = {}  # station name -> capacity or None
        self._order = {}  # station name -> "oldest" or "newest"
        self._history = []  # copies of the state from before each recorded call

    def add_station(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("station name must be a non-empty str")
        if name in self._stations:
            raise DockError(f"station {name!r} already exists")
        self._save()
        self._stations[name] = []
        self._capacity[name] = None
        self._order[name] = self._default_order

    def dock(self, station, bike):
        self._require(station)
        if not isinstance(bike, str) or not bike:
            raise ValueError("bike id must be a non-empty str")
        if bike in self._where:
            raise DockError(f"bike {bike!r} is already docked")
        self._require_room(station, 1)
        self._save()
        self._put(station, [bike])

    def undock(self, bike):
        if not isinstance(bike, str) or bike not in self._where:
            raise KeyError(bike)
        self._save()
        station = self._where.pop(bike)
        self._stations[station].remove(bike)

    def rebalance(self, from_station, to_station, count):
        self._require(from_station)
        self._require(to_station)
        check_count(count)
        if from_station == to_station:
            raise ValueError("cannot rebalance a station into itself")
        bikes = self._stations[from_station]
        if len(bikes) < count:
            raise DockError(f"station {from_station!r} has fewer than {count} bikes")
        self._save()
        if self._order[from_station] == "newest":
            moved = bikes[len(bikes) - count :]
            del bikes[len(bikes) - count :]
        else:
            moved = bikes[:count]
            del bikes[:count]
        self._put(to_station, moved)

    def close_station(self, name, into):
        self._require(name)
        self._require(into)
        if name == into:
            raise ValueError("cannot close a station into itself")
        self._require_room(into, len(self._stations[name]))
        self._save()
        moved = self._stations.pop(name)
        del self._capacity[name]
        del self._order[name]
        self._put(into, moved)
        return len(moved)

    def set_capacity(self, station, capacity):
        self._require(station)
        if capacity is not None and (
            isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0
        ):
            raise ValueError(f"capacity must be None or a positive int, got {capacity!r}")
        self._save()
        self._capacity[station] = capacity

    def get_capacity(self, station):
        self._require(station)
        return self._capacity[station]

    def set_take_order(self, station, order):
        self._require(station)
        check_order(order)
        self._save()
        self._order[station] = order

    def get_take_order(self, station):
        self._require(station)
        return self._order[station]

    def undo(self):
        if not self._history:
            raise DockError("nothing to undo")
        self._stations, self._where, self._capacity, self._order = self._history.pop()

    def get_bikes(self, station):
        self._require(station)
        return list(self._stations[station])

    def get_station_of(self, bike):
        if not isinstance(bike, str) or bike not in self._where:
            raise KeyError(bike)
        return self._where[bike]

    def get_stations(self):
        return list(self._stations)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        state = (self._stations, self._where, self._capacity, self._order)
        self._history.append(copy.deepcopy(state))

    def _require_room(self, station, count):
        capacity = self._capacity[station]
        if count and capacity is not None and len(self._stations[station]) + count > capacity:
            raise StationFull(f"station {station!r} has no room for {count} more bikes")

    def _put(self, station, bikes):
        self._stations[station].extend(bikes)
        for bike in bikes:
            self._where[bike] = station

    def _require(self, station):
        if not isinstance(station, str) or station not in self._stations:
            raise KeyError(station)
