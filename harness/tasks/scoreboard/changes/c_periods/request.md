Split the match in `scoreboard.py` into numbered periods (halves, quarters,
innings and so on), and report the score per period.

- The match starts in period 1. Add `Scoreboard.next_period() -> int`,
  which starts the next period and returns its number, and
  `Scoreboard.get_period() -> int`, which returns the number of the current
  period.
- Each scoring event belongs to the period that was current when it was
  scored. `get_score` still counts every period together.
- Add `Scoreboard.get_period_scores(team) -> list[int]`: the team's points
  in each period from period 1 up to the current period, in period order,
  with 0 for a period in which it scored nothing. It raises `KeyError` for
  a team that was not added.
- `get_events` takes a new keyword argument `period=None`. `None` returns
  every event, as before. Otherwise only the events of that period are
  returned, oldest first.
- Add `Scoreboard.get_period_standings(period) -> list[str]`: every team,
  ordered by the points it scored in that period, highest first; teams with
  equal points stay in the order they were added.
- A period passed to `get_events` or `get_period_standings` must be an
  `int` from 1 up to the current period (not `bool`), or `ValueError` is
  raised. In `get_events`, a team that was not added (`KeyError`) is
  reported before a bad period.
- `undo_last` takes the event back from the period it was scored in, even
  when a later period has started since.

All existing behavior must keep working.
