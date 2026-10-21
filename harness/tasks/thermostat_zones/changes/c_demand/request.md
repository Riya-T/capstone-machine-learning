Report how far each zone in `thermostat.py` is from its target, so the
boiler controller can see the heating and cooling demand.

- Add `Thermostat.get_demand(zone) -> int`. For a zone in mode `"heat"`
  it is the target minus the most recent reading; in mode `"cool"` it is
  the most recent reading minus the target. A negative result counts as 0.
  A zone in mode `"off"`, or one with no reading yet, has a demand of 0.
- Add `Thermostat.get_total_demand() -> int`: the sum of `get_demand` over
  every zone.
- Add `Thermostat.get_calls(zone) -> int`: how many of the zone's readings
  so far had a demand greater than 0 at the moment they were recorded,
  worked out with the mode and target in force at that moment. Later
  changes to the mode or target do not alter the count of past readings.
- `get_demand` and `get_calls` raise `KeyError` for a zone that was not
  added.

All existing behavior must keep working.
