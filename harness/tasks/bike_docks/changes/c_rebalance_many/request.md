Let a dispatcher in `bikes.py` plan a round of rebalancing as one job that
is carried out completely or not at all.

- Add `BikeNetwork.rebalance_many(moves) -> int`. `moves` is a `list` of
  `(from_station, to_station, count)` tuples. The moves are carried out in
  the order given, each exactly like `rebalance(from_station, to_station,
  count)`, and each sees the bikes as the moves before it left them (a
  bike moved by one move can be moved again by a later one).
- It returns how many bikes the moves moved in total, counting a bike
  again each time a later move moves it.
- If any move would raise (with the same error `rebalance` would raise for
  it at that point), `rebalance_many` raises that error and changes
  nothing: the moves before it are not carried out either, so every
  station's bikes are exactly as they were before the call.
- What an empty list does is unspecified.

All existing behavior must keep working.
