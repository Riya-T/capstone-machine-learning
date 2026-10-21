Add a limit on wrong guesses to `hangman.py`, so that a game can be lost.

- `start_game` takes a new keyword argument `max_wrong=None`. `None` means
  no limit, as before. Otherwise it must be an `int` of 1 or more (not a
  `bool`); anything else raises `ValueError` and no game is started. When
  the id, the word or the limit are invalid together, any of the
  `ValueError`s may come first; `HangmanError` for an id already in use is
  still raised after every `ValueError` check.
- When a wrong guess brings a game's wrong count up to its limit, the game's
  status becomes `"lost"`. That guess still counts like any other: `guess`
  returns `False`, the letter is listed by `get_guesses` and counted by
  `get_wrong_count`.
- A lost game is over, exactly like a won one: `guess` raises `HangmanError`
  and changes nothing. The same error order applies: `KeyError`, then
  `ValueError` for a bad letter, then `HangmanError`.
- Add `Hangman.get_max_wrong(game_id) -> int | None`: the game's limit, or
  `None` when it has none.
- Add `Hangman.get_guesses_left(game_id) -> int | None`: the limit minus the
  wrong count, or `None` when the game has no limit. It is 0 for a lost game.
- Both new methods raise `KeyError` for a game id that is not in use.

All existing behavior must keep working.
