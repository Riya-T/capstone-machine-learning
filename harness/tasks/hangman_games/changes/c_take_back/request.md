Let a guess be taken back in `hangman.py`, for a player who hit the wrong
key.

- Add `Hangman.take_back(game_id) -> str`: removes the game's most recent
  guess and returns the letter that was removed. Afterwards the game is
  exactly as if that guess had never been made: the letter is gone from
  `get_guesses`, `get_progress` and `get_wrong_count` no longer reflect it,
  and a game that this guess had finished is `"playing"` again.
- `take_back` raises `KeyError` for a game id that is not in use, then
  `HangmanError` when the game has no guesses left to take back. In both
  cases nothing changes.
- Calling `take_back` several times removes guesses newest first, so taking
  back every guess returns the game to the state it started in.
- A letter that was taken back may be guessed again.

All existing behavior must keep working.
