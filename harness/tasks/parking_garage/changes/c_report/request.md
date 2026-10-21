Add usage figures to `garage.py`.

- Add `Garage.get_report() -> list[tuple[str, int, int, int]]`: one tuple
  per level, in the order the levels were added, of the form
  `(level_id, parked, stays, minutes)`. `parked` is the number of vehicles
  on the level right now, `stays` the number of vehicles that have left the
  level so far, and `minutes` the total of the parking times returned by
  those `leave` calls. A vehicle that enters, leaves and comes back counts
  one stay per visit.
- Add `Garage.get_peak(level_id) -> int`: the largest number of vehicles
  that were parked on the level at the same time since it was added, or 0
  for a level no vehicle has used. It raises `KeyError` for a level that was
  not added, including non-str values.
- A call that raises changes no figure.

All existing behavior must keep working.
