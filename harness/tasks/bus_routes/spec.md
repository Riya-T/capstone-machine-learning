# Bus routes

Write a module `network.py` that keeps track of a city's bus routes. Each
route is an ordered list of stops, from its first stop to its last, and
routes are edited as stops open, close and lines are cut in two.

## Interface

```python
class RouteError(Exception): ...


class BusNetwork:
    def __init__(self): ...
    def add_route(self, name: str) -> None: ...
    def remove_route(self, name: str) -> None: ...
    def add_stop(self, route: str, stop: str) -> None: ...
    def remove_stop(self, route: str, stop: str) -> None: ...
    def retire_stop(self, stop: str) -> int: ...
    def split_route(self, route: str, at_stop: str, new_route: str) -> int: ...
    def get_routes(self) -> list[str]: ...
    def get_stops(self, route: str) -> list[str]: ...
```

Route names and stop names are non-empty strings.

## Routes

- `add_route(name)` adds a route with no stops. A name that is already in
  use raises `RouteError`.
- `get_routes()` returns the names of the routes in use, in the order they
  were added.
- `remove_route(name)` removes the route together with all of its stops.
  The name is then free: `add_route` may add it again later, as a new route
  with no stops, at the end of `get_routes()`.
- `remove_route`, `add_stop`, `remove_stop`, `get_stops`, and the `route`
  argument of `split_route`, raise `KeyError` for a route name that is not
  in use: one that was never added, or one that was removed.

## Stops

- `add_stop(route, stop)` adds `stop` at the end of the route. A route has
  each stop at most once: adding a stop the route already has raises
  `RouteError`. The same stop may be on several routes.
- `get_stops(route)` returns the route's stops in order, from first to last
  (an empty list for a route with no stops).
- `remove_stop(route, stop)` removes `stop` from the route; the other stops
  keep their order. A stop that is not on the route raises `RouteError`.
- `retire_stop(stop)` removes `stop` from every route that has it, and
  returns how many routes it was removed from. On each route the other
  stops keep their order. If no route has the stop, nothing changes and it
  returns 0.
- `split_route(route, at_stop, new_route)` cuts a route in two: `at_stop`
  and every stop after it move, in the same order, to a new route named
  `new_route`, which is added at the end of `get_routes()`. The moved stops
  are no longer on `route`; the stops before `at_stop` stay there. If
  `at_stop` was the first stop, `route` keeps no stops but stays in use. It
  returns how many stops moved.
  It raises `RouteError` if `at_stop` is not on `route`, or if `new_route`
  is a name already in use (`route` itself included).

## Errors

A failed call has no effect: if a method raises, the list of routes and the
stops of every route are unchanged.

When a call has more than one problem, which error it raises is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes route or stop names that are not non-empty strings (such as `""`,
`None` or `1`), which error a call with several problems raises, what
happens if a returned list is changed, the text of error messages, saving
the network to a file, and use from several threads.
