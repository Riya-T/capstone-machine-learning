"""Bus routes with several stops added in one call, and undo.

Planted bug (after c_add_stops and c_undo): undo was added correctly, but
add_stops was rewritten to save the state and then add the stops one by
one, checking each only when its turn comes, so a refused stop leaves the
stops listed before it on the route.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from network import BusNetwork
    net = BusNetwork()
    net.add_route("red")
    net.add_stop("red", "depot")
    net.undo()  # red has no stops again
"""


class RouteError(Exception):
    pass


class BusNetwork:
    def __init__(self):
        # route name -> list of stops in order, in the order routes were added
        self._routes = {}
        self._undo_stack = []  # copies of the routes as they were before each call

    def add_route(self, name):
        if name in self._routes:
            raise RouteError(f"route name {name!r} is already used")
        self._save()
        self._routes[name] = []

    def remove_route(self, name):
        self._stops(name)
        self._save()
        del self._routes[name]

    def add_stop(self, route, stop):
        stops = self._stops(route)
        if stop in stops:
            raise RouteError(f"route {route!r} already has stop {stop!r}")
        self._save()
        stops.append(stop)

    def add_stops(self, route, new_stops):
        stops = self._stops(route)
        self._save()  # one call, one undo
        for stop in new_stops:
            if stop in stops:
                raise RouteError(f"route {route!r} already has stop {stop!r}")
            stops.append(stop)
        return len(new_stops)

    def remove_stop(self, route, stop):
        stops = self._stops(route)
        self._require_stop(route, stop)
        self._save()
        stops.remove(stop)

    def retire_stop(self, stop):
        having = [stops for stops in self._routes.values() if stop in stops]
        self._save()
        for stops in having:
            stops.remove(stop)
        return len(having)

    def split_route(self, route, at_stop, new_route):
        stops = self._stops(route)
        self._require_stop(route, at_stop)
        if new_route in self._routes:
            raise RouteError(f"route name {new_route!r} is already used")
        self._save()
        cut = stops.index(at_stop)
        self._routes[new_route] = stops[cut:]
        del stops[cut:]
        return len(self._routes[new_route])

    def undo(self):
        if not self._undo_stack:
            raise RouteError("nothing to undo")
        self._routes = self._undo_stack.pop()

    def get_routes(self):
        return list(self._routes)

    def get_stops(self, route):
        return list(self._stops(route))

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: list(stops) for name, stops in self._routes.items()})

    def _stops(self, route):
        if route not in self._routes:
            raise KeyError(route)
        return self._routes[route]

    def _require_stop(self, route, stop):
        if stop not in self._routes[route]:
            raise RouteError(f"route {route!r} has no stop {stop!r}")
