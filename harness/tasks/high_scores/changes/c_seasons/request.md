Split the scores in `scores.py` into seasons.

- The board always has a current season. A new board's current season is
  called `"default"`. Every score is recorded into the season that is
  current at the time.
- Add `ScoreBoard.start_season(season)`: makes `season` the new current
  season. It must be a non-empty `str`, or `ValueError` is raised; a name
  already used for a season (including `"default"`) raises `ScoreError`.
  Starting a season adds no players and changes no scores.
- Add `ScoreBoard.get_seasons() -> list[str]`: every season in the order
  started, beginning with `"default"`. Add
  `ScoreBoard.get_current_season() -> str`.
- `get_scores`, `get_total_score`, `get_top_scores`, `get_personal_best` and
  `get_leaderboard` take a new keyword argument `season=None`. With `None`
  they cover every season, exactly as before. With a season name they use
  only the scores recorded in that season: `get_personal_best` raises
  `ScoreError` for a player with no score in that season, and
  `get_leaderboard` leaves such players out. A season name that was never
  started raises `KeyError`.
- Players are shared by all seasons: `get_players()` is unchanged, and
  `get_latest_score` still returns the most recent score of any season.
- When a call has several problems, `KeyError` for the player comes first,
  then `ValueError` for `n`, then `KeyError` for the season.

All existing behavior must keep working.
