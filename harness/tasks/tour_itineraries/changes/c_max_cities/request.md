Limit the tours in `tours.py` to 8 cities, because a tour bus can only
manage so many stops.

- Add `class TourFull(TourError)` to `tours.py`.
- A tour may have at most 8 cities. A call that would leave a tour with
  more than 8 cities raises `TourFull` and changes nothing:
  - `add_city` on a tour that already has 8 cities;
  - `merge_tours` when `first` would end up with more than 8 cities,
    counted after skipping the cities `first` already has (so merging
    tours that share cities may still fit); tour `second` is then not
    removed;
  - any other method that adds cities to a tour, for every tour it would
    add cities to.
- `remove_city` and `cancel_city` never raise `TourFull`, and a tour with
  8 cities works as before in every other way.
- When a call has another problem as well (a tour that is not in use, a
  city already on the tour, the same tour twice), which error is raised is
  unspecified.
- `undo` still restores the exact earlier state, as before; it is never
  blocked by the limit.

All existing behavior must keep working.
