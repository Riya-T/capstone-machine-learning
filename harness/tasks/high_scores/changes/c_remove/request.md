Let scores be taken off the board in `scores.py`, for example after a
mistyped entry.

- Add `ScoreBoard.remove_score(name, score)`: removes the player's most
  recently recorded occurrence of that score; earlier occurrences and other
  scores stay. It raises `KeyError` for a name that is not on the board and
  `ValueError` for a score that `record_score` would reject. For a player on
  the board and a valid score, it raises `ScoreError` if the player has no
  occurrence of that score left. Which error is raised when a call has
  several of these problems is unspecified. Nothing changes when it raises.
- Add `ScoreBoard.undo_last_score() -> tuple[str, int]`: removes the most
  recently recorded score still on the board, whichever player it belongs
  to, and returns `(name, score)`. A board with no scores left raises
  `ScoreError`.
- After a removal, `get_scores`, `get_latest_score`, `get_total_score` and
  `get_top_scores` behave as if the removed score had never been recorded.
  Removals are not themselves recorded: after `remove_score`,
  `undo_last_score` removes the most recent of the scores that remain.

For example, suppose `"ana"` records 50, then `"ben"` records 70, then
`"ana"` records 80 and then 50 again:

- `undo_last_score()` returns `("ana", 50)` and leaves `get_scores("ana")`
  as `[50, 80]`.
- If instead `remove_score("ana", 50)` is called, `get_scores("ana")` is
  `[50, 80]` (not `[80, 50]`). `undo_last_score()` then returns
  `("ana", 80)`, and the next call returns `("ben", 70)`.

All existing behavior must keep working.
