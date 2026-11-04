Timing officials sometimes fix a lap time after the fact, and several
officials may work on the race at once. Add corrections with version checks
to `telemetry.py`, so an official working from an outdated view of the race
is stopped instead of silently overwriting someone else's work.

- Add `class VersionConflict(TelemetryError)` to `telemetry.py`.
- The race has a version number. It is 1 when the `RaceTelemetry` is
  created and goes up by 1 with every successful `record_lap` or
  `correct_lap`. Failed calls do not change it. Add
  `RaceTelemetry.get_version() -> int`.
- Add `RaceTelemetry.correct_lap(car_id, lap_number, lap_time,
  expected_version=None)`, which replaces the time of the car's lap number
  `lap_number` (1 is its first lap) with `lap_time`.
  - It raises `KeyError` for a car that was not added.
  - The lap must already be recorded: a `lap_number` below 1 or above the
    number of laps the car has recorded raises `ValueError`, and so does a
    new lap time of 0 or less.
  - A finished car can be corrected, and the results and points follow the
    corrected time.
- `record_lap` takes a new keyword argument `expected_version=None`.
- For both methods, when `expected_version` is not `None` and differs from
  the race's current version, `VersionConflict` is raised and nothing
  changes. With `None` no version check is done.

For example, after two laps of red the version is 3;
`correct_lap("red", 2, 91000, expected_version=3)` replaces red's second
lap and makes it 4, and the same call again raises `VersionConflict`.

Which error `correct_lap` or `record_lap` raises when one call has several
problems (for example an invalid lap time, or a car that has finished,
together with an `expected_version` that does not match) is unspecified.

All existing behavior must keep working.
