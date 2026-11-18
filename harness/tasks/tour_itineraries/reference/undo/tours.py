"""Tour itineraries with undo.

Correct solution for tour_itineraries after c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from tours import TourPlanner
    planner = TourPlanner()
    planner.add_tour("coast")
    planner.add_city("coast", "lisbon")
    planner.undo()  # coast has no cities again
"""


class TourError(Exception):
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
        self._save()
        added = [city for city in self._tours[second] if city not in self._tours[first]]
        self._tours[first].extend(added)
        del self._tours[second]
        return len(added)

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

    def _require(self, tour):
        if not isinstance(tour, str) or tour not in self._tours:
            raise KeyError(tour)
