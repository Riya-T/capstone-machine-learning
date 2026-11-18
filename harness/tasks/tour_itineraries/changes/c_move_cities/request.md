Let a planner move several cities from one tour to another in one go in
`tours.py`, so that the move happens completely or not at all.

- Add `TourPlanner.move_cities(source, target, cities) -> None`. `cities`
  is a list of city names. Each of them is removed from tour `source` and
  added at the end of tour `target`, in the order of the list. The cities
  that stay on `source` keep their order, and so do the cities `target`
  already had.
- It raises, and then changes nothing at all (no city moves), when:
  - `source` or `target` is not a tour in use: `KeyError`;
  - `source` and `target` are the same tour: `ValueError`;
  - a city in the list is not on `source`, is already on `target`, or is
    in the list more than once: `TourError`.

  When several of these apply, which error is raised is unspecified.
- An empty list, and values of `cities` that are not a list of strings,
  are unspecified.

All existing behavior must keep working.
