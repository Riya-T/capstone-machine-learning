Let a zone in `thermostat.py` be put on hold, so a schedule or a tenant
cannot change its setting while, for example, a room is being painted.

- Add `Thermostat.hold(zone)`, `Thermostat.release(zone)` and
  `Thermostat.is_held(zone) -> bool`. All three raise `KeyError` for a
  zone that was not added. New zones are not held. Holding a held zone, or
  releasing one that is not held, does nothing.
- Add `class ZoneHeld(ThermostatError)` to `thermostat.py`.
- While a zone is held, `set_target` and `set_mode` raise `ZoneHeld` and
  change nothing. Readings are still recorded, and every method that only
  reads data keeps working.
- `ZoneHeld` is raised after every `KeyError` and `ValueError` check that
  the call already makes, and before any other `ThermostatError`.
- Holding and releasing do not change the zone's mode, target or readings.

All existing behavior must keep working.
