"""Bike docks with undo and station capacities.

Correct solution for bike_docks after c_undo and c_capacity. Never shown to
the writer or the editor; validate-tasks checks that it passes every test it
should.

Usage:
    from bikes import BikeNetwork
    net = BikeNetwork()
    net.add_station("north")
    net.set_capacity("north", 1)
    net.dock("north", "b1")
    net.undo()  # north is empty again
"""

import copy


class DockError(Exception):
    pass


class StationFull(DockError):
    pass


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


class BikeNetwork:
    def __init__(self):
        # station name -> list of bikes in the order they arrived; the dict
        # keeps the stations in the order they were added.
        self._stations = {}
        self._where = {}  # bike -> name of the station it is docked at
        self._capacity = {}  # station name -> capacity or None
        self._history = []  # copies of the state from before each recorded call

    def add_station(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("station name must be a non-empty str")
        if name in self._stations:
            raise DockError(f"station {name!r} already exists")
        self._save()
        self._stations[name] = []
        self._capacity[name] = None

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
        self._require_room(to_station, count)
        self._save()
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

    def undo(self):
        if not self._history:
            raise DockError("nothing to undo")
        self._stations, self._where, self._capacity = self._history.pop()

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
        self._history.append(copy.deepcopy((self._stations, self._where, self._capacity)))

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
