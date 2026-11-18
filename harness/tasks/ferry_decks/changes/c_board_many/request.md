Let `ferry.py` board a group of vehicles in one call, such as the cars of
one booking, so that either the whole group comes aboard or none of it.

- Add `Ferry.board_many(arrivals) -> int`. `arrivals` is a non-empty list of
  `(vehicle, deck)` tuples. `board_many` boards each vehicle onto its deck,
  as `board(vehicle, deck)` would, one tuple after another in the order
  given, and returns how many vehicles it boarded.
- The group boards as a whole: if any tuple would make `board` raise (a
  deck that was never added, or a vehicle that is already aboard),
  `board_many` raises that same error and changes nothing at all, not even
  for the tuples before it.
- Each tuple sees the vehicles boarded by the tuples before it: a vehicle
  name that appears twice in `arrivals` raises `FerryError`, since the
  second tuple would board a vehicle that is already aboard.
- Vehicles that board the same deck go on in the order of `arrivals`, after
  the vehicles already on that deck.
- When several tuples would raise, which error is raised is unspecified. An
  empty list is unspecified.

All existing behavior must keep working.
