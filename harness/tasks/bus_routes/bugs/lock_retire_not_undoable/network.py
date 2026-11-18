"""Bus routes with undo and locked routes.

Planted bug (after c_undo and c_lock): locked routes were added correctly,
but retire_stop, rewritten to check every route's lock before removing the
stop anywhere, no longer records itself, so undo skips it and reverses the
call before it instead.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from network import BusNetwork
    net = BusNetwork()
    net.add_route("red")
    net.add_stop("red", "depot")
    net.lock_route("red")
    net.undo()  # red is unlocked again
"""


class RouteError(Exception):
    pass


class RouteLocked(RouteError):
    pass


class BusNetwork:
    def __init__(self):
        # route name -> list of stops in order, in the order routes were added
        self._routes = {}
        self._locked = set()  # names of the locked routes
        self._undo_stack = []  # (routes, locked) as they were before each call

    def add_route(self, name):
        if name in self._routes:
            raise RouteError(f"route name {name!r} is already used")
        self._save()
        self._routes[name] = []

    def remove_route(self, name):
        self._unlocked_stops(name)
        self._save()
        del self._routes[name]

    def add_stop(self, route, stop):
        stops = self._unlocked_stops(route)
        if stop in stops:
            raise RouteError(f"route {route!r} already has stop {stop!r}")
        self._save()
        stops.append(stop)

    def remove_stop(self, route, stop):
        stops = self._unlocked_stops(route)
        self._require_stop(route, stop)
        self._save()
        stops.remove(stop)

    def retire_stop(self, stop):
        having = [name for name, stops in self._routes.items() if stop in stops]
        for name in having:  # every route is checked before any changes
            self._require_unlocked(name)
        for name in having:
            self._routes[name].remove(stop)
        return len(having)

    def split_route(self, route, at_stop, new_route):
        stops = self._unlocked_stops(route)
        self._require_stop(route, at_stop)
        if new_route in self._routes:
            raise RouteError(f"route name {new_route!r} is already used")
        self._save()
        cut = stops.index(at_stop)
        self._routes[new_route] = stops[cut:]
        del stops[cut:]
        return len(self._routes[new_route])

    def lock_route(self, route):
        self._stops(route)
        self._save()
        self._locked.add(route)

    def unlock_route(self, route):
        self._stops(route)
        self._save()
        self._locked.discard(route)

    def is_locked(self, route):
        self._stops(route)
        return route in self._locked

    def undo(self):
        if not self._undo_stack:
            raise RouteError("nothing to undo")
        self._routes, self._locked = self._undo_stack.pop()

    def get_routes(self):
        return list(self._routes)

    def get_stops(self, route):
        return list(self._stops(route))

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        routes = {name: list(stops) for name, stops in self._routes.items()}
        self._undo_stack.append((routes, set(self._locked)))

    def _stops(self, route):
        if route not in self._routes:
            raise KeyError(route)
        return self._routes[route]

    def _unlocked_stops(self, route):
        stops = self._stops(route)
        self._require_unlocked(route)
        return stops

    def _require_unlocked(self, route):
        if route in self._locked:
            raise RouteLocked(f"route {route!r} is locked")

    def _require_stop(self, route, stop):
        if stop not in self._routes[route]:
            raise RouteError(f"route {route!r} has no stop {stop!r}")
