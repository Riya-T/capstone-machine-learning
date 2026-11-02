Add hints to `hangman.py`, for players who are stuck.

- Add `Hangman.get_hint(game_id) -> str`: a letter of the word that has not
  been guessed yet. When several letters are still missing, it is the one
  that occurs most often in the word; among letters that occur equally
  often, it is the one whose first occurrence comes earliest in the word.
  For the word `banana` with nothing guessed the hint is `a`; after `a` is
  guessed it is `n`, then `b`. Wrong guesses do not change the hint.
- `get_hint` raises `KeyError` for a game id that is not in use, and
  `HangmanError` when the game is over (won or lost), since there is no
  point in a hint.
- Add `Hangman.get_missing_count(game_id) -> int`: how many different
  letters of the word have not been guessed yet. It is 0 for a won game,
  and still counts the letters left in a lost game. Raises `KeyError` for a
  game id that is not in use.
- Asking for a hint or the missing count changes nothing: the guesses, the
  wrong count, the progress and the status stay exactly as they were, and
  asking again gives the same answer until a guess is made.

All existing behavior must keep working.
