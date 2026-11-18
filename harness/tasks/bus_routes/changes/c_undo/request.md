Add an undo to `network.py`, so a mistake in editing the routes can be
taken back.

- Add `BusNetwork.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among the calls that change the
  network: `add_route`, `remove_route`, `add_stop`, `remove_stop`,
  `retire_stop` and `split_route`, and any method added later that changes
  the network. Each further `undo` goes one call further back.
- Undoing a call puts the list of routes, in its order, and the stops of
  every route, in their order, back exactly as they were just before that
  call:
  - an undone `remove_route` brings the route back with all its stops, at
    its original position in `get_routes()`; its name is in use again;
  - an undone `remove_stop` puts the stop back at its original position on
    the route, and an undone `retire_stop` puts it back at its original
    position on every route it was removed from;
  - an undone `split_route` puts the moved stops back at the end of the
    route they came from and removes the new route; its name is free again;
  - an undone `add_route` removes the route, and its name may then be added
    again.
- A call that changes several routes at once (`retire_stop`, `split_route`)
  is one call: a single `undo` reverses all of it. A `retire_stop` that
  removed the stop from no route is still a call: `undo` reverses it like
  any other, which changes nothing.
- Calls that raised are not recorded, so `undo` skips them. Calls to the
  `get_` methods and to `undo` itself are not recorded either and are never
  undone. There is no redo.
- With nothing left to undo, `undo` raises `RouteError` and changes nothing.

All existing behavior must keep working.
