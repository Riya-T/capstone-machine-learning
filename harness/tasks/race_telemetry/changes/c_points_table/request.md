Let the organizers of a race choose how many points each place scores in
`telemetry.py`, instead of the fixed table 10, 6, 4, 3, 2, 1.

- `RaceTelemetry` takes a new keyword argument
  `points_table=(10, 6, 4, 3, 2, 1)`: the points for 1st place, 2nd place,
  and so on. Every place past the end of the table scores 0. A table must
  be a `list` or `tuple` whose items are 0 or more. It may be empty, in
  which case no place scores. Anything else, such as `10`, `"10,6"` or
  `[10, -1]`, raises `ValueError`.
- Add `RaceTelemetry.set_points_table(points_table)`, which replaces the
  table. An invalid table raises `ValueError` and changes nothing.
- Add `RaceTelemetry.get_points_table() -> list[int]`, the table in force,
  as a list.
- `get_results` scores every place with the table in force when it is
  called, including cars that finished before the table was set. For
  example, with `points_table=[25, 18]` and three finished cars,
  `get_results()` gives 25, 18 and 0 points; after
  `set_points_table([5])` it gives 5, 0 and 0.

Which error is raised when `RaceTelemetry(...)` gets both an invalid number
of laps and an invalid table is unspecified. All existing behavior must
keep working.
