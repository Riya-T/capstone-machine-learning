Let routes in `network.py` be locked, for example while a route's
timetable is being printed, so that nothing changes its stops by accident.

- Add `BusNetwork.lock_route(route)`, `BusNetwork.unlock_route(route)` and
  `BusNetwork.is_locked(route) -> bool`. All three raise `KeyError` for a
  route that is not in use. Locking a locked route, or unlocking a route
  that is not locked, does nothing.
- Add `class RouteLocked(RouteError)` to `network.py`.
- New routes are not locked. That includes the route made by
  `split_route`, and a route added again under the name of a removed one.
- No call may change the stops of a locked route or remove it. A call that
  would raises `RouteLocked` and changes nothing:
  - `add_stop`, `remove_stop`, `remove_route` and `split_route` on a locked
    route (for `split_route`, the route being cut);
  - `retire_stop` when any route that has the stop is locked: then the stop
    is removed from no route at all, not even from the routes that are not
    locked.
- `retire_stop` of a stop that no locked route has works as before, even
  while other routes are locked. `get_routes` and `get_stops` work as
  before on locked routes.
- When a call also has another problem (a route not in use, a stop that is
  or is not on the route, a name in use), which error it raises is
  unspecified.
- `undo` still puts back exactly the state from before the call it
  reverses, including which routes are locked: `lock_route` and
  `unlock_route` are recorded and undone like the other calls that change
  the network.

All existing behavior must keep working.
