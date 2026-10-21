Make the point values in `scoreboard.py` adjustable, so the same scoreboard
can be used for other sports and other rule sets.

- `Scoreboard` takes a new keyword argument `points=None`. `None` keeps the
  standard table (`"try"` 5, `"conversion"` 2, `"drop_goal"` 3). Otherwise
  it is a `dict` from kind to points that replaces the standard table, so
  only its kinds can be scored. It must be a non-empty `dict` whose keys are
  non-empty strings and whose values are `int`s of 1 or more (not `bool`);
  anything else raises `ValueError`. Changing that dict after passing it in
  has no effect on the scoreboard.
- Add `Scoreboard.get_points(kind) -> int`: what the kind is worth right
  now. A kind that is not in the table raises `ValueError`.
- Add `Scoreboard.get_kinds() -> list[str]`: the kinds that can be scored,
  in the order they entered the table (the order of the dict passed in, or
  of the standard table, then kinds added with `set_points`).
- Add `Scoreboard.set_points(kind, value)`: from now on the kind is worth
  `value`. A kind that is not in the table yet is added to it. The kind
  must be a non-empty string and the value an `int` of 1 or more (not
  `bool`), or `ValueError` is raised and nothing changes.
- An event keeps the points it was worth when it was scored: `set_points`
  changes neither `get_score` nor `get_events` for events already recorded.
- Each scoreboard has its own table: changing one never changes another.

All existing behavior must keep working.
