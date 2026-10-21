Add per-zone limits on the target temperature to `thermostat.py`, so a
tenant cannot set a bedroom to 35 degrees.

- Add `Thermostat.set_limits(zone, low, high)`. Both must be `int`s (not
  `bool`) with `low <= high`, or `ValueError` is raised. If the zone's
  current target is below `low` or above `high`, `ThermostatError` is
  raised instead and the limits are not changed. Calling it again replaces
  the zone's limits, under the same rules.
- Add `Thermostat.get_limits(zone) -> tuple[int, int] | None`: the zone's
  `(low, high)`, or `None` for a zone whose limits were never set.
- Once a zone has limits, `set_target` with a temperature below `low` or
  above `high` raises `ValueError` and the target is unchanged. `low` and
  `high` themselves are allowed. A zone without limits accepts any `int`.
- Limits apply to targets only: `record_reading` is never limited.
- Both new methods raise `KeyError` for a zone that was not added, then
  `ValueError`, then `ThermostatError`. In each case nothing changes.

All existing behavior must keep working.
