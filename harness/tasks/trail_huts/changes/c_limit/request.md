Let huts in `trails.py` limit how many trails lead to them, since a small
hut cannot take walkers arriving from every direction.

- `add_hut` takes a new keyword argument: `add_hut(name, max_trails=None)`.
  `None` means the hut has no limit. Otherwise `max_trails` is an `int`
  greater than 0: the most trails the hut may have. A limit of 0 or less
  raises `ValueError` and adds no hut.
- Add `TrailMap.get_max_trails(hut) -> int | None`. It returns the hut's
  limit (`None` for no limit) and raises `KeyError` for a hut that is not
  in use.
- Add `class TooManyTrails(TrailError)` to `trails.py`.
- A hut never has more trails than its limit:
  - `add_trail` raises `TooManyTrails` and changes nothing when either of
    the two huts already has as many trails as its limit;
  - `merge_huts` raises `TooManyTrails` and changes nothing (the merged
    hut is not removed either) when `into_hut` would end up with more
    trails than its limit. The other huts keep as many trails as they had,
    so their limits are not checked.
- Ending up with exactly as many trails as the limit is allowed.
- `remove_trail` and `close_hut` never check limits.
- A hut added under the name of a closed or merged hut gets the limit
  given in its own `add_hut` call, not the old hut's.
- `undo` still puts back the exact earlier state, limits included: an
  undone `close_hut` brings the hut back with its limit, and after an
  undone `add_hut` the name may be added again with any limit.
- When a call has more than one problem, which error is raised is
  unspecified.

All existing behavior must keep working.
