"""Tour itineraries with undo and an adjustable limit of cities per tour.

Planted bug (after c_undo, c_max_cities and c_max_setting): per-tour
limits work, but merge_tours, reworked to use the limit of `first`, now
counts every city of `second`, including those `first` already has, so a
merge of tours that share cities can be refused although it fits.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from tours import TourPlanner
    planner = TourPlanner(max_cities=3)
    planner.add_tour("coast")
    planner.set_max_cities("coast", None)  # no limit for this tour
"""


class TourError(Exception):
    pass


class TourFull(TourError):
    pass


def check_limit(limit):
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError(f"limit must be None or an int of 1 or more, got {limit!r}")


class TourPlanner:
    def __init__(self, max_cities=8):
        check_limit(max_cities)
        self._default_limit = max_cities
        # tour name -> its cities in order; the tours are kept in the order
        # they were added.
        self._tours = {}
        self._limits = {}  # tour name -> its limit (None = no limit)
        self._history = []  # snapshots of the state just before each recorded call

    def add_tour(self, name):
        if name in self._tours:
            raise TourError(f"tour name {name!r} is already used")
        self._save()
        self._tours[name] = []
        self._limits[name] = self._default_limit

    def add_city(self, tour, city):
        self._require(tour)
        if city in self._tours[tour]:
            raise TourError(f"{city!r} is already on tour {tour!r}")
        self._require_room(tour, len(self._tours[tour]) + 1)
        self._save()
        self._tours[tour].append(city)

    def remove_city(self, tour, city):
        self._require(tour)
        if city not in self._tours[tour]:
            raise TourError(f"{city!r} is not on tour {tour!r}")
        self._save()
        self._tours[tour].remove(city)

    def cancel_city(self, city):
        self._save()
        removed = 0
        for cities in self._tours.values():
            if city in cities:
                cities.remove(city)
                removed += 1
        return removed

    def merge_tours(self, first, second):
        self._require(first)
        self._require(second)
        if first == second:
            raise ValueError("cannot merge a tour into itself")
        added = [city for city in self._tours[second] if city not in self._tours[first]]
        self._require_room(first, len(self._tours[first]) + len(self._tours[second]))
        self._save()
        self._tours[first].extend(added)
        del self._tours[second]
        del self._limits[second]
        return len(added)

    def set_max_cities(self, tour, limit):
        self._require(tour)
        check_limit(limit)
        if limit is not None and limit < len(self._tours[tour]):
            raise ValueError(f"tour {tour!r} already has more than {limit} cities")
        self._save()
        self._limits[tour] = limit

    def get_max_cities(self, tour):
        self._require(tour)
        return self._limits[tour]

    def undo(self):
        if not self._history:
            raise TourError("nothing to undo")
        self._tours, self._limits = self._history.pop()

    def get_cities(self, tour):
        self._require(tour)
        return list(self._tours[tour])

    def get_tours(self):
        return list(self._tours)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        tours = {name: list(cities) for name, cities in self._tours.items()}
        self._history.append((tours, dict(self._limits)))

    def _require_room(self, tour, count):
        limit = self._limits[tour]
        if limit is not None and count > limit:
            raise TourFull(f"tour {tour!r} may have at most {limit} cities")

    def _require(self, tour):
        if not isinstance(tour, str) or tour not in self._tours:
            raise KeyError(tour)
