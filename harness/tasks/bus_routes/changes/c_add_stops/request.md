Let a route in `network.py` be extended by several stops in one call, for
example when a planned extension of a line opens all at once.

- Add `BusNetwork.add_stops(route, stops) -> int`. `stops` is a list of one
  or more stop names. They are added at the end of the route, in the order
  given, and the call returns how many stops it added.
- It raises `KeyError` for a route that is not in use.
- The call succeeds or fails as a whole. If any stop in the list is
  already on the route, or the list names the same stop more than once,
  it raises `RouteError` and adds none of the stops, not even the ones
  listed before the problem.
- Stops added by `add_stops` are ordinary stops: the other methods treat
  them exactly like stops added one at a time with `add_stop`.

All existing behavior must keep working.
