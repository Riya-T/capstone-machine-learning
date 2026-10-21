Let scores be taken off the board in `scores.py`, for example after a
mistyped entry.

- Add `ScoreBoard.remove_score(name, score)`: removes the player's most
  recently recorded occurrence of that score; earlier occurrences and other
  scores stay. It raises `KeyError` for a name that is not on the board,
  then `ValueError` for a score that `record_score` would reject, then
  `ScoreError` if the player has not recorded that score. Nothing changes
  when it raises.
- Add `ScoreBoard.undo_last_score() -> tuple[str, int]`: removes the most
  recently recorded score still on the board, whichever player it belongs
  to, and returns `(name, score)`. A board with no scores left raises
  `ScoreError`.
- After a removal, `get_scores`, `get_latest_score`, `get_total_score` and
  `get_top_scores` behave as if the removed score had never been recorded.
  Removals are not themselves recorded: after `remove_score`,
  `undo_last_score` removes the most recent of the scores that remain.

All existing behavior must keep working.
