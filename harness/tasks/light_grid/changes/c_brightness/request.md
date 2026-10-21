Give the lights in `lights.py` brightness levels instead of just on and
off, with the number of levels set per grid and the size of each step set
per command.

- `LightGrid` takes a new keyword argument `max_brightness=1`. It must be
  an `int` that is 1 or more (not a `bool`); anything else raises
  `ValueError`.
- Every light has a brightness from 0 to `max_brightness`. Every light
  starts at 0. A light is on when its brightness is more than 0, and off
  at 0.
- `turn_on` and `turn_off` take a new keyword argument `step=1`, which must
  be an `int` that is 1 or more (not a `bool`), or `ValueError` is raised.
  `turn_on` raises the brightness of every light in the rectangle by
  `step`, but never above `max_brightness`. `turn_off` lowers it by `step`,
  but never below 0.
- `toggle` sets every light at 0 to `max_brightness`, and every light above
  0 to 0.
- Add `LightGrid.get_brightness(x, y) -> int`, which returns one light's
  brightness, and `LightGrid.get_total_brightness() -> int`, which returns
  the sum of the brightness of all lights.
- `is_on`, `get_lit_count` and every other method that reports which lights
  are on count a light as on when its brightness is more than 0.
- With `max_brightness=1` and `step=1` every command behaves exactly as
  before.
- Bad coordinates and a bad `step` both raise `ValueError`. A failed call
  changes nothing.

All existing behavior must keep working.
