Add per-zone limits on the target temperature to `thermostat.py`, so a
tenant cannot set a bedroom to 35 degrees.

- Add `Thermostat.set_limits(zone, low, high)`. Both must be `int`s with
  `low <= high`, or `ValueError` is raised (so `set_limits(zone, 26, 25)`
  raises `ValueError`). If the limits are valid but the zone's current
  target is below `low` or above `high`, `ThermostatError` is raised and the
  limits are not changed. Calling it again replaces the zone's limits, under
  the same rules.
- Add `Thermostat.get_limits(zone) -> tuple[int, int] | None`: the zone's
  `(low, high)`, or `None` for a zone whose limits were never set.
- Once a zone has limits, `set_target` with a temperature below `low` or
  above `high` raises `ValueError` and the target is unchanged. `low` and
  `high` themselves are allowed. A zone without limits accepts any `int`.
- Limits apply to targets only: `record_reading` is never limited.
- Both new methods raise `KeyError` for a zone that was not added. In each
  case nothing changes.
- Which error `set_limits` raises when one call has several of these
  problems (for example a zone that was not added and bounds that are not
  `int`s) is unspecified.

All existing behavior must keep working.
