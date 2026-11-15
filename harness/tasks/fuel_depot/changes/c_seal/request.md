Let tanks in `depot.py` be sealed, for example while a tank is inspected.

- Add `Depot.seal(tank_id)` and `Depot.unseal(tank_id)`. Both raise
  `KeyError` for an id that is not a tank in use. New tanks are not sealed.
  Sealing a sealed tank, or unsealing one that is not sealed, does nothing.
- Add `class Sealed(DepotError)` to `depot.py`.
- A sealed tank takes no part in any movement of fuel: `fill`, `drain`,
  `pump`, `pump_down` and `retire_tank` raise `Sealed` and change nothing
  when any tank named in the call is sealed, whether it would give fuel or
  take it. This holds even when the call would move 0 litres (a `pump_down`
  with nothing above `keep`, or retiring an empty tank).
- `Sealed` is checked after the `KeyError` and `ValueError` checks
  (including the one for the same tank on both sides) and before every
  other error.
- Calls that move no fuel work on sealed tanks as before: `add_tank`, every
  `get_...` method, and every other method.
- Sealing and unsealing add nothing to any log.

All existing behavior must keep working.
