Make the limit of 8 cities per tour in `tours.py` adjustable: some tours
travel by minibus, and some have no bus at all.

- `TourPlanner` takes a new keyword argument `max_cities=8`: the limit
  every new tour starts with. It must be `None`, meaning no limit, or an
  `int` of 1 or more; anything else raises `ValueError`.
- Add `TourPlanner.set_max_cities(tour, limit)` and
  `TourPlanner.get_max_cities(tour) -> int | None`. Both raise `KeyError`
  for a tour that is not in use. `limit` follows the same rule as
  `max_cities`, and a limit smaller than the number of cities the tour has
  now raises `ValueError` as well; in each case nothing changes. When
  `set_max_cities` has problems of both kinds, which error is raised is
  unspecified. `set_max_cities` changes only that tour's limit.
- Every tour starts with the planner's `max_cities` when it is added. That
  includes a tour added again under the name of a merged one: it does not
  keep the old tour's limit.
- Every rule that used the limit of 8 now uses the tour's own limit, and
  `None` means no limit: `add_city`, `merge_tours` (the limit of `first`,
  counted as before), and any other method that adds cities to a tour.
- `undo` still restores the exact earlier state, now including every
  tour's limit: `set_max_cities` is a recorded call like the others, so
  `undo` reverses it.

All existing behavior must keep working.
