Add a limit on wrong guesses to `hangman.py`, so that a game can be lost,
and stop games that are over from taking more guesses.

- `start_game` takes a new keyword argument `max_wrong=None`. With the
  default `None` the game has no limit: however many wrong guesses are
  made, it is never lost, stays `"playing"` and can still be won.
- Otherwise `max_wrong` must be an `int` of 1 or more. Anything else, such
  as `0`, `-1`, `2.5` or `"3"`, raises `ValueError`, and no game is
  started.
- A game with a limit is lost at the wrong guess that brings its wrong
  count up to its `max_wrong`: from then on `get_status` returns `"lost"`.
  That guess still counts like any other: `guess` returns `False`, the
  letter is listed by `get_guesses` and counted by `get_wrong_count`. For
  example, with `max_wrong=2` and the word `cab`, guessing `x` leaves the
  game `"playing"`, and guessing `y` then loses it. Right guesses never
  count towards the limit.
- A game that is won or lost is over. `guess` in a game that is over raises
  `HangmanError` and changes nothing, whatever the letter, including letters
  never guessed before. For example, with the word `cab`, after guessing
  `c`, `a` and `b` the game is won, and guessing `z` then raises
  `HangmanError`. With `max_wrong=1`, guessing `z` loses the game, and
  guessing `c` then raises `HangmanError`.
- Add `Hangman.get_max_wrong(game_id) -> int | None`: the game's limit, or
  `None` when it has none.
- Add `Hangman.get_guesses_left(game_id) -> int | None`: the limit minus the
  wrong count, or `None` when the game has no limit. It is 0 for a lost
  game.
- Both new methods raise `KeyError` for a game id that is not in use.
- Which error is raised when a call has several problems stays unspecified,
  and so do `bool` values as `max_wrong`.

All existing behavior must keep working.
