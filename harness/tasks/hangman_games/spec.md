# Hangman games

Write a module `hangman.py` that runs several games of hangman at the same
time. Each game has a name, a secret word and the letters guessed so far.
A game is won by guessing every letter of its word.

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
  `a` to `z`; anything else raises `ValueError`. Starting a game with an id
  that is already in use raises `HangmanError`.
- `get_games()` returns the ids of all games, in the order they were started.
- Every other method raises `KeyError` when given a game id that is not in
  use, including values that are not strings at all, such as `None` or `1`.

## Guessing

- `guess(game_id, letter)` records a guess. The letter must be a `str` of
  exactly one lowercase letter `a` to `z`, or `ValueError` is raised.
- `guess` returns `True` when the letter occurs in the word and `False`
  otherwise. A guess whose letter does not occur in the word is a wrong
  guess.
- Guessing a letter that was already guessed in this game raises
  `HangmanError`.

## Winning

Every game starts with the status `"playing"`.

- The guess that reveals the last hidden letter wins the game: the status
  becomes `"won"`. For the word `cab`, after guessing `c`, `a` and `b` the
  status is `"won"`. A one-letter word such as `q` is won by guessing `q`.
- Wrong guesses made on the way do not stop a win: for the word `cab`,
  after guessing `d`, `e`, `f`, `g` and `h` the status is still `"playing"`
  with 5 wrong guesses, and guessing `c`, `a` and `b` then wins the game.
- `get_status(game_id)` returns the game's status: `"playing"` until the
  game is won, and `"won"` from then on.

## Reading a game

- `get_progress(game_id)` returns a string with one character per letter of
  the word, in order: the letter itself if it has been guessed, and `_`
  otherwise. For the word `banana` after guessing `a`, it is `_a_a_a`.
- `get_guesses(game_id)` returns the letters guessed so far, right and
  wrong, in alphabetical order: after guessing `z`, `b`, `a`, `n` it is
  `["a", "b", "n", "z"]`.
- `get_wrong_count(game_id)` returns how many of the game's guesses were
  wrong.

A failed call has no effect: if a method raises, every game is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes what happens to a game once it has 6 or more wrong guesses (its
status, and whether it takes more guesses); what `guess` does in a game
that is already won; which error is raised when a call has several problems
(such as a game id not in use together with a bad letter); ids that are not
strings passed to `start_game`; words and letters that are neither a `str`
nor `None`; whether the word can be read back; what happens if a returned
list is changed; the text of error messages; saving the games to a file;
and use from several threads.
