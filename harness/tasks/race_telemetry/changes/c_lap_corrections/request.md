Timing officials sometimes fix a lap time after the fact, and several
officials may work on the same race at once. Add corrections with version
checks to `telemetry.py`, so an official working from an outdated view of
a race is stopped instead of silently overwriting someone else's work.

- Add `class VersionConflict(TelemetryError)` to `telemetry.py`.
- Every race has a version number. It is 1 when the race is added and goes
  up by 1 with every successful `record_lap` or `correct_lap` in that race.
  Failed calls do not change it. Add
  `RaceTelemetry.get_version(race_id) -> int`, which raises `KeyError` for
  an unknown race.
- Add `RaceTelemetry.correct_lap(race_id, car_id, lap_number, lap_time,
  expected_version=None)`, which replaces the time of the car's lap number
  `lap_number` in that race (1 is its first lap) with `lap_time`. The lap
  must already be recorded: a `lap_number` that is not an `int`, or not
  between 1 and the number of laps the car has recorded there, raises
  `ValueError`, and so does an invalid `lap_time` (same rule as for
  `record_lap`). Results and points follow the corrected time. A finished
  car can be corrected.
- `record_lap` takes a new keyword argument `expected_version=None`.
- For both methods, when `expected_version` is not `None` and differs from
  the race's current version, `VersionConflict` is raised and nothing
  changes. With `None` no version check is done.

When `correct_lap` has several problems, the first of these is raised:
`KeyError` for an unknown race or car, then `ValueError` (for either
argument), then `VersionConflict`. For `record_lap` the order is
`KeyError`, `ValueError`, `VersionConflict`, and last the
`TelemetryError` for a finished car.

All existing behavior must keep working.
