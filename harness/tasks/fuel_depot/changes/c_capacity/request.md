Give the tanks in `depot.py` a capacity, so no tank is ever filled past what
it can hold.

- Add `Depot.set_capacity(tank_id, litres)` and
  `Depot.get_capacity(tank_id) -> int | None`. Every tank's capacity starts
  as `None`, which means no limit. A capacity must be an `int` that is 0 or
  more, or `None`; anything else raises `ValueError`. Both methods raise
  `KeyError` for an id that is not a tank in use (`set_capacity` checks the
  id before the capacity). Setting a capacity adds nothing to any log.
- A capacity may be set below the tank's current level. The level stays as
  it is; the tank can still give fuel, but takes no more until its level
  plus what goes in fits within the capacity again.
- Add `class Overflow(DepotError)` to `depot.py`.
- Every call that puts fuel into a tank raises `Overflow` if that tank's
  level after the call would be above its capacity. This covers `fill`, and
  the receiving tank (`to_id`) of `pump`, `pump_down` and `retire_tank`.
  Like any call that raises, a call that raises `Overflow` has no effect at
  all; in particular, a `retire_tank` that raises leaves the tank in use.
- `pump_down` and `retire_tank` never move less to make room: they move
  exactly what they moved before, or raise `Overflow`. A movement of 0
  litres never raises `Overflow`, even into a tank that is above its
  capacity. The sending tank's capacity plays no part.
- `Overflow` is checked after every existing check: when a call also has
  another problem (a tank that is not in use, an invalid `litres` or
  `keep`, the same tank on both sides, or not enough fuel), that error is
  raised instead.

All existing behavior must keep working.
