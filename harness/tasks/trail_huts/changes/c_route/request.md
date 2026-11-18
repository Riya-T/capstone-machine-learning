Let a whole new route be marked on the map in `trails.py` with one call
that adds all of its trails or none of them.

- Add `TrailMap.add_route(huts) -> None`. `huts` is a list of hut names.
  It adds a trail between each hut in the list and the next one: the
  first and the second, the second and the third, and so on, in that
  order.
- Each of these trails follows the rules of `add_trail`: a hut that is not
  in use raises `KeyError`; the same hut twice in a row raises
  `ValueError`; two huts that are already joined raise `TrailError`, and
  that includes two huts joined by an earlier trail of the same route.
  A hut may appear more than once in a route as long as no trail repeats,
  such as `["A", "B", "C", "A"]`.
- If any of the trails cannot be added, `add_route` raises that error and
  adds no trail at all.
- The new trails are added in route order, so each comes last in the
  neighbors of its two huts at the moment it is added, just as with
  `add_trail` calls made one after another.
- A list of fewer than two huts, and which error is raised when a call
  has more than one problem, are unspecified.

All existing behavior must keep working.
