Let the scorer in `scoreboard.py` take back scoring events that were entered
by mistake.

- Add `Scoreboard.undo_last(team) -> tuple[str, int]`. It takes back the
  team's most recent event that has not been taken back yet and returns it
  as a `(kind, points)` tuple. The event disappears from `get_events`, the
  team's score drops by exactly the points that event was worth when it was
  scored (even if `set_points` has changed that kind since), and
  `get_standings` follows the new score.
- Calling it again takes back the event before that one, and so on. For a
  team with no events left it raises `ScoreboardError` and changes nothing.
  For a team that was not added it raises `KeyError`.
- Add `Scoreboard.get_undone(team) -> list[tuple[str, int]]`: the events
  taken back from that team, in the order they were taken back, as
  `(kind, points)` tuples. It raises `KeyError` for a team that was not
  added.
- Taking back an event only affects that team. Events scored after an undo
  are recorded as usual, and an event that was taken back never returns.

All existing behavior must keep working.
