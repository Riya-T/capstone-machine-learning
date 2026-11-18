"""Bus routes with several stops added in one call.

Correct solution for bus_routes after c_add_stops.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from network import BusNetwork
    net = BusNetwork()
    net.add_route("red")
    net.add_stops("red", ["depot", "market"])  # 2
"""


class RouteError(Exception):
    pass


class BusNetwork:
    def __init__(self):
        # route name -> list of stops in order, in the order routes were added
        self._routes = {}

    def add_route(self, name):
        if name in self._routes:
            raise RouteError(f"route name {name!r} is already used")
        self._routes[name] = []

    def remove_route(self, name):
        self._stops(name)
        del self._routes[name]

    def add_stop(self, route, stop):
        stops = self._stops(route)
        if stop in stops:
            raise RouteError(f"route {route!r} already has stop {stop!r}")
        stops.append(stop)

    def add_stops(self, route, new_stops):
        stops = self._stops(route)
        # Every stop is checked before any is added.
        if len(set(new_stops)) != len(new_stops):
            raise RouteError("the list names a stop more than once")
        for stop in new_stops:
            if stop in stops:
                raise RouteError(f"route {route!r} already has stop {stop!r}")
        stops.extend(new_stops)
        return len(new_stops)

    def remove_stop(self, route, stop):
        stops = self._stops(route)
        self._require_stop(route, stop)
        stops.remove(stop)

    def retire_stop(self, stop):
        having = [stops for stops in self._routes.values() if stop in stops]
        for stops in having:
            stops.remove(stop)
        return len(having)

    def split_route(self, route, at_stop, new_route):
        stops = self._stops(route)
        self._require_stop(route, at_stop)
        if new_route in self._routes:
            raise RouteError(f"route name {new_route!r} is already used")
        cut = stops.index(at_stop)
        self._routes[new_route] = stops[cut:]
        del stops[cut:]
        return len(self._routes[new_route])

    def get_routes(self):
        return list(self._routes)

    def get_stops(self, route):
        return list(self._stops(route))

    def _stops(self, route):
        if route not in self._routes:
            raise KeyError(route)
        return self._routes[route]

    def _require_stop(self, route, stop):
        if stop not in self._routes[route]:
            raise RouteError(f"route {route!r} has no stop {stop!r}")
