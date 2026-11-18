Add an undo to `bikes.py`, so a dispatcher's mistake can be taken back.

- Add `BikeNetwork.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among `add_station`, `dock`, `undock`,
  `rebalance`, `close_station`, and any other method that changes the
  stations or their bikes, including methods added later. Each further
  `undo` goes one call further back.
- Undoing a call puts the list of stations, and every station's bikes in
  their order, back to exactly what they were just before that call. A
  call that changed several things is undone as a whole:
  - an undone `undock` puts the bike back at its old position in its
    station's list, and it is docked again;
  - an undone `rebalance` puts the moved bikes back at the front of
    `from_station`'s list, in their old order, and takes them off
    `to_station`;
  - an undone `close_station` brings the closed station back, with its
    bikes in their old order and at its old position in `get_stations()`,
    and takes those bikes off the station they were moved to; its name is
    in use again;
  - an undone `add_station` removes the station, and its name may then be
    added again;
  - `get_station_of` follows: every bike is reported at the station where
    it was docked before the undone call.
- A `close_station` that moved 0 bikes is still a call: `undo` reverses it
  like any other (the empty station comes back).
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `DockError` and changes nothing.

All existing behavior must keep working.
