Let recorded games in `season.py` be looked up and removed, for example when
a result is overturned.

- Add `Season.remove_game(game_id)`. Afterwards every record and the
  standings are exactly as if the game had never been recorded.
- Add `Season.get_game(game_id) -> dict` with the keys `home`, `away`,
  `home_score` and `away_score`.
- Both raise `KeyError` for an id that is not a recorded game: one that was
  never returned by `record_game`, one that was already removed, or a value
  that is not an `int`. Nothing changes when they raise.
- Ids are never reused: after a removal, the next recorded game still gets
  the next new id.

All existing behavior must keep working.
