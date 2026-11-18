Make it adjustable in `bikes.py` which bikes `rebalance` takes from a
station, because some operators move the bikes docked most recently
instead of the ones that have waited longest.

- `BikeNetwork` takes a new keyword argument `take_order="oldest"`. It
  must be `"oldest"` or `"newest"`; anything else raises `ValueError`.
- Every station has a take order. A new station gets the network's
  `take_order`.
- Add `BikeNetwork.get_take_order(station) -> str` and
  `BikeNetwork.set_take_order(station, order)`, which replaces the
  station's take order. Both raise `KeyError` for a station that is not in
  use; `set_take_order` raises `ValueError` for an order other than
  `"oldest"` or `"newest"`. In each case nothing changes. Which error is
  raised when both are wrong is unspecified.
- `rebalance(from_station, to_station, count)` uses the take order of
  `from_station`:
  - `"oldest"` takes the first `count` bikes of `get_bikes(from_station)`,
    as before;
  - `"newest"` takes the last `count` bikes of `get_bikes(from_station)`.

  Either way the moved bikes keep their order (earliest first) and go to
  the end of `to_station`'s list, and the bikes left at `from_station`
  keep theirs. The take order of `to_station` does not matter, and every
  other rule of `rebalance` (including capacities) stays the same.
- `close_station` moves every bike as before, whatever the take order.
- `undo` still puts back exactly the state from before the undone call:
  `set_take_order` is a call that `undo` reverses like any other, and an
  undone `close_station` brings the station back with its take order.
  `set_take_order` changes no bikes.

All existing behavior must keep working.
