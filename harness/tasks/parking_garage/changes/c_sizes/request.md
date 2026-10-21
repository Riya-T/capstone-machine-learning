Give vehicles and levels a size in `garage.py`, so a vehicle only parks on
a level it fits on.

- The sizes are the strings `"small"`, `"medium"` and `"large"`, in that
  order from smallest to largest.
- `add_level` takes a new keyword argument `max_size="large"`: the largest
  vehicle size the level accepts. A value that is not one of the three sizes
  raises `ValueError` and no level is added.
- `enter` takes a new keyword argument `size="medium"`: the size of the
  vehicle. A value that is not one of the three sizes raises `ValueError`
  and nothing changes.
- A vehicle fits on a level when its size is not larger than the level's
  `max_size`. `enter` parks the vehicle on the first level, in the order the
  levels were added, that has a free spot and that the vehicle fits on.
  Levels the vehicle does not fit on are skipped even when they have free
  spots. When there is no such level, `GarageFull` is raised.
- Add `Garage.get_max_size(level_id) -> str`, which returns the level's
  `max_size`. It raises `KeyError` for a level that was not added,
  including non-str values.
- Add `Garage.get_size(plate) -> str`, which returns the size of a parked
  vehicle. It raises `KeyError` for a plate that is not parked, including
  non-str values.

Error order for `enter`: `ValueError` for a bad plate, minute or size (in
any order among those three), then `GarageError` for a plate that is already
parked, then `GarageFull`. For `add_level`: `ValueError` for any bad
argument, then `GarageError` for an id that was already added. All existing
behavior must keep working.
