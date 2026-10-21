Detect conflicting updates in `scoreboard.py`: two scorers' devices may send
events for the same team, each based on what it last saw.

- Each team has a version number. It is 1 when the team is added and goes
  up by 1 with every successful `score` for that team. Failed calls never
  change it, and scoring for one team leaves every other team's version as
  it was.
- Add `Scoreboard.get_version(team) -> int`. It raises `KeyError` for a team
  that was not added.
- Add `class VersionConflict(ScoreboardError)` to `scoreboard.py`.
- `score` takes a new keyword argument `expected_version=None`. When it is
  given and is not the team's current version, `score` raises
  `VersionConflict` and records nothing. `None` means no check is made.
- When a call to `score` has several problems, they are reported in this
  order: `KeyError` for the team, then `ValueError` for the kind, then
  `VersionConflict`.

All existing behavior must keep working.
