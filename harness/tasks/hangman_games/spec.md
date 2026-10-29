# Hangman games

Write a module `hangman.py` that runs several games of hangman at the same
time. Each game has a name, a secret word and the letters guessed so far.

## Interface

```python
class HangmanError(Exception): ...


class Hangman:
    def __init__(self): ...
    def start_game(self, game_id: str, word: str) -> None: ...
    def guess(self, game_id: str, letter: str) -> bool: ...
    def get_progress(self, game_id: str) -> str: ...
    def get_guesses(self, game_id: str) -> list[str]: ...
    def get_wrong_count(self, game_id: str) -> int: ...
    def get_status(self, game_id: str) -> str: ...
    def get_games(self) -> list[str]: ...
```

## Games

- `start_game(game_id, word)` starts a game. The id must be a non-empty
  `str` and the word a non-empty `str` made only of the lowercase letters
  `a` to `z`; anything else raises `ValueError` (if both are invalid, either
  `ValueError` may be raised). Starting a game with an id that is already in
  use raises `HangmanError`. A `ValueError` is raised before a `HangmanError`.
- `get_games()` returns the ids of all games, in the order they were started.
- Every other method raises `KeyError` when given a game id that is not in
  use, including values that are not strings at all, such as `None` or `1`.

## Guessing

- `guess(game_id, letter)` records a guess. The letter must be a `str` of
  exactly one lowercase letter `a` to `z`, or `ValueError` is raised.
- A guess is refused with `HangmanError` when the game is already won, or
  when the same letter was already guessed in this game.
- `guess` returns `True` when the letter occurs in the word and `False`
  otherwise.
- When a call has several problems, the first of these is raised:
  `KeyError` for a game id not in use, then `ValueError` for a bad letter,
  then `HangmanError`.

## Reading a game

- `get_progress(game_id)` returns a string with one character per letter of
  the word, in order: the letter itself if it has been guessed, and `_`
  otherwise. For the word `banana` after guessing `a`, it is `_a_a_a`.
- `get_guesses(game_id)` returns the letters guessed so far, in the order
  they were guessed (not sorted): after guessing `z`, `b`, `a`, `n` it is
  `["z", "b", "a", "n"]`.
- `get_wrong_count(game_id)` returns how many guesses were letters that do
  not occur in the word.
- `get_status(game_id)` returns `"playing"` until every letter of the word
  has been guessed, and `"won"` from then on. Wrong guesses never end a
  game.

A failed call has no effect: if a method raises, every game is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `start_game`, whether the word
can be read back, what happens if a returned list is changed, the text of
error messages, saving the games to a file, and use from several threads.
