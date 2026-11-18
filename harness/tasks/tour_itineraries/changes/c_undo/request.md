Add an undo to `tours.py`, so a planner's mistake can be taken back.

- Add `TourPlanner.undo() -> None`. It reverses the most recent successful
  call that has not been undone yet among `add_tour`, `add_city`,
  `remove_city`, `cancel_city` and `merge_tours`, and any other method
  that changes the tours (including methods added later). Each further
  `undo` goes one call further back.
- Undoing a call puts the list of tours, and every tour's cities in their
  order, back exactly as they were just before that call:
  - an undone `remove_city` puts the city back at its old position on the
    tour;
  - an undone `cancel_city` puts the city back at its old position on
    every tour it was removed from;
  - an undone `merge_tours` takes the added cities off `first` and brings
    tour `second` back, with its cities in their order and at its old
    position in `get_tours()`; its name is in use again;
  - an undone `add_tour` removes the tour, and its name may be added
    again; an undone `add_city` removes the city from the tour.
- A call that changes several things at once is one call: one `undo`
  reverses all of it. A `merge_tours` that added 0 cities is still a call:
  `undo` brings tour `second` back.
- A `cancel_city` that returned 0 changed nothing; you may record it as a
  call or skip it, either is fine.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `TourError` and changes
  nothing.

All existing behavior must keep working.
