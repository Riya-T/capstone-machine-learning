"""Bike docks: which bikes are docked at which station, in docking order.

Planted bug (initial spec): close_station moves the bikes into `into` but
does not update where each bike is docked, so get_station_of still reports
the closed station for them. Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from bikes import BikeNetwork
    net = BikeNetwork()
    net.add_station("north")
    net.add_station("south")
    net.dock("north", "b1")
    net.rebalance("north", "south", 1)
"""


class DockError(Exception):
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

    def add_station(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("station name must be a non-empty str")
        if name in self._stations:
            raise DockError(f"station {name!r} already exists")
        self._stations[name] = []

    def dock(self, station, bike):
        self._require(station)
        if not isinstance(bike, str) or not bike:
            raise ValueError("bike id must be a non-empty str")
        if bike in self._where:
            raise DockError(f"bike {bike!r} is already docked")
        self._put(station, [bike])

    def undock(self, bike):
        if not isinstance(bike, str) or bike not in self._where:
            raise KeyError(bike)
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
        moved = bikes[:count]
        del bikes[:count]
        self._put(to_station, moved)

    def close_station(self, name, into):
        self._require(name)
        self._require(into)
        if name == into:
            raise ValueError("cannot close a station into itself")
        moved = self._stations.pop(name)
        self._stations[into].extend(moved)
        return len(moved)

    def get_bikes(self, station):
        self._require(station)
        return list(self._stations[station])

    def get_station_of(self, bike):
        if not isinstance(bike, str) or bike not in self._where:
            raise KeyError(bike)
        return self._where[bike]

    def get_stations(self):
        return list(self._stations)

    def _put(self, station, bikes):
        self._stations[station].extend(bikes)
        for bike in bikes:
            self._where[bike] = station

    def _require(self, station):
        if not isinstance(station, str) or station not in self._stations:
            raise KeyError(station)
