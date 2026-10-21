Add personal bests to `scores.py`.

- Add `ScoreBoard.get_personal_best(name) -> int`: the highest score the
  player has recorded. A player with no scores raises `ScoreError`.
- Add `ScoreBoard.get_personal_best_count(name) -> int`: how many of the
  player's scores were a new personal best when they were recorded, that is,
  strictly higher than every score the player had recorded before. The
  player's first score always counts; a score equal to the best so far does
  not. A player with no scores has a count of 0.
- Add `ScoreBoard.get_leaderboard() -> list[tuple[str, int]]`: one
  `(name, personal_best)` pair for every player with at least one score,
  highest personal best first. Players with the same personal best keep the
  order they were added in. Players without scores are left out; an empty
  board gives `[]`.
- `get_personal_best` and `get_personal_best_count` raise `KeyError` for a
  name that is not on the board.
- These values are computed from the scores on the board at the time of the
  call. If the board lets scores be removed, a removed score counts as never
  having been recorded.

All existing behavior must keep working.
