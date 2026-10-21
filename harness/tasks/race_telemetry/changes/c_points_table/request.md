Let the organizers of a series choose how many points each place scores in
`telemetry.py`, both for the whole series and for single races (for
example a season finale worth double points).

- `RaceTelemetry` takes a new keyword argument
  `points_table=(10, 6, 4, 3, 2, 1)`: the points for 1st place, 2nd place,
  and so on. Every place past the end of the table scores 0. A table must
  be a `list` or `tuple` whose items are `int`s of 0 or more (not `bool`s).
  It may be empty, in which case no place scores. Anything else raises
  `ValueError`.
- `add_race` takes a new keyword argument `points_table=None`. With `None`
  the race scores with the series table; otherwise it scores with its own
  table, checked the same way. If several arguments of `add_race` are
  invalid, any of the `ValueError`s may come first; all of them come before
  `TelemetryError` for a race id that is already in use. If `add_race`
  raises, no race is added.
- Add `RaceTelemetry.set_points_table(points_table)`, which replaces the
  series table. An invalid table raises `ValueError` and changes nothing.
  Races without their own table always score with the series table in
  force when points are asked for, including races added before the change
  and races that are already over.
- Add `RaceTelemetry.get_points_table(race_id=None) -> list[int]`. With no
  race id it returns the series table; with a race id, the table that race
  scores with. An unknown race id raises `KeyError`.
- `get_points` scores each race with that race's table.

All existing behavior must keep working.
