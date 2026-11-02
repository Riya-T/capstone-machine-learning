Let a guess be taken back in `hangman.py`, for a player who hit the wrong
key.

- Add `Hangman.take_back(game_id) -> str`: removes the game's most recent
  guess, the latest one `guess` recorded that has not been taken back yet,
  and returns its letter. Afterwards the game is exactly as if that guess
  had never been made: the letter is gone from `get_guesses`, and
  `get_progress` and `get_wrong_count` no longer reflect it.
- This works in a game that is won too: a game that this guess had won is
  `"playing"` again.
- Calling `take_back` several times removes guesses newest first, whatever
  their alphabetical order, so taking back every guess returns the game to
  the state it started in. For the word `banana`, after guessing `n`, `z`
  and `b`, `take_back` returns `b`, then `z`, then `n`.
- `take_back` raises `KeyError` for a game id that is not in use, and
  `HangmanError` when the game has no guesses left to take back. In both
  cases nothing changes.
- A letter that was taken back may be guessed again.

All existing behavior must keep working.
