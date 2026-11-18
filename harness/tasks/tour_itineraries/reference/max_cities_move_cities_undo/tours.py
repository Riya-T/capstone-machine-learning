"""Tour itineraries with moving several cities as one call, undo and at
most 8 cities per tour.

Correct solution for tour_itineraries after c_move_cities, c_undo and
c_max_cities. Never shown to the writer or the editor; validate-tasks
checks that it passes every test it should.

Usage:
    from tours import TourPlanner
    planner = TourPlanner()
    planner.add_tour("coast")
    planner.add_tour("alps")
    planner.add_city("coast", "lyon")
    planner.move_cities("coast", "alps", ["lyon"])  # alps may hold 8
"""

MAX_CITIES = 8


class TourError(Exception):
    pass


class TourFull(TourError):
    pass


class TourPlanner:
    def __init__(self):
        # tour name -> its cities in order; the tours are kept in the order
        # they were added.
        self._tours = {}
        self._history = []  # snapshots of the state just before each recorded call

    def add_tour(self, name):
        if name in self._tours:
            raise TourError(f"tour name {name!r} is already used")
        self._save()
        self._tours[name] = []

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
        self._require_room(first, len(self._tours[first]) + len(added))
        self._save()
        self._tours[first].extend(added)
        del self._tours[second]
        return len(added)

    def move_cities(self, source, target, cities):
        self._check_move(source, target, cities)
        self._require_room(target, len(self._tours[target]) + len(cities))
        self._save()
        for city in cities:
            self._tours[source].remove(city)
        self._tours[target].extend(cities)

    def undo(self):
        if not self._history:
            raise TourError("nothing to undo")
        self._tours = self._history.pop()

    def get_cities(self, tour):
        self._require(tour)
        return list(self._tours[tour])

    def get_tours(self):
        return list(self._tours)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._history.append({name: list(cities) for name, cities in self._tours.items()})

    def _check_move(self, source, target, cities):
        # Every check comes before any city moves.
        self._require(source)
        self._require(target)
        if source == target:
            raise ValueError("cannot move cities to the tour they are on")
        if len(set(cities)) != len(cities):
            raise TourError("a city is listed more than once")
        for city in cities:
            if city not in self._tours[source]:
                raise TourError(f"{city!r} is not on tour {source!r}")
            if city in self._tours[target]:
                raise TourError(f"{city!r} is already on tour {target!r}")

    def _require_room(self, tour, count):
        if count > MAX_CITIES:
            raise TourFull(f"tour {tour!r} may have at most {MAX_CITIES} cities")

    def _require(self, tour):
        if not isinstance(tour, str) or tour not in self._tours:
            raise KeyError(tour)
