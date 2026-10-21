Let parts of the grid in `lights.py` be locked, so that commands leave them
alone, for example while the lights there are being repaired.

- Add `LightGrid.lock(x1, y1, x2, y2)` and `LightGrid.unlock(x1, y1, x2, y2)`,
  which lock and unlock every light in the rectangle (corners included, as
  for the other commands). Locking a light that is locked, or unlocking one
  that is not, does nothing. A new grid has no locked lights.
- Add `LightGrid.is_locked(x, y) -> bool` and
  `LightGrid.get_locked_count() -> int`, the number of locked lights.
- `turn_on`, `turn_off` and `toggle` leave every locked light exactly as it
  is, and change the other lights in the rectangle as usual. A rectangle
  that contains locked lights is not an error.
- Locking and unlocking never change whether a light is on, or how bright
  it is.
- The new methods take coordinates by the same rules as the other methods
  and raise `ValueError` for bad ones, changing nothing.

All existing behavior must keep working.
