Give stations in `bikes.py` a capacity, because a station only has so many
docks.

- Add `class StationFull(DockError)` to `bikes.py`.
- Add `BikeNetwork.set_capacity(station, capacity)` and
  `BikeNetwork.get_capacity(station) -> int | None`. Both raise `KeyError`
  for a station that is not in use.
- `capacity` is either `None`, meaning no limit, or an `int` greater than
  0, the most bikes the station may hold. Anything else raises
  `ValueError` and changes nothing. Each call replaces the station's
  earlier capacity. Every new station starts with `None`.
- Every call that puts bikes at a station checks that the station would
  not end up with more bikes than its capacity: `dock`, the receiving
  station of `rebalance` (`to_station`) and of `close_station` (`into`),
  and any other method that puts bikes at a station, including methods
  added later. If it would, the call raises `StationFull` and changes
  nothing: no bike moves, and `close_station` does not close the station.
- A capacity does not affect bikes already at the station: setting a
  capacity below the number of bikes there is allowed, the bikes stay, and
  they can be undocked or moved away as before. The capacity of the station
  the bikes leave is never checked.
- When a call would raise `StationFull` and also has another problem, which
  error is raised is unspecified.
- `undo` still puts back exactly the state from before the undone call:
  `set_capacity` is a call that `undo` reverses like any other, and an
  undone `close_station` brings the station back with its capacity.
  `set_capacity` changes no bikes.

All existing behavior must keep working.
