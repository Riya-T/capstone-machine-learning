# High scores

Write a module `scores.py` that keeps a board of players and the scores they
have recorded in a game.

## Interface

```python
class ScoreError(Exception): ...


class ScoreBoard:
    def __init__(self): ...
    def add_player(self, name: str) -> None: ...
    def record_score(self, name: str, score: int) -> None: ...
    def get_players(self) -> list[str]: ...
    def get_scores(self, name: str) -> list[int]: ...
    def get_latest_score(self, name: str) -> int: ...
    def get_total_score(self, name: str) -> int: ...
    def get_top_scores(self, n: int) -> list[int]: ...
```

All scores are whole points, as `int`.

## Players

- `add_player(name)` adds a player with no scores. An empty name raises
  `ValueError`, and a name that is already on the board raises `ScoreError`.
- `get_players()` returns the names of all players, in the order they were
  added.
- Every other method that takes a name raises `KeyError` when the name is
  not on the board, including values that are not strings at all, such as
  `None` or `1`.

## Scores

- `record_score(name, score)` records a score for the player. A score must be
  an `int` of 0 or more, or `ValueError` is raised. The same player may record
  the same score many times.
- `get_scores(name)` returns the player's scores in the order they were
  recorded, including repeats.
- `get_latest_score(name)` returns the player's most recently recorded score.
  A player with no scores raises `ScoreError`.
- `get_total_score(name)` returns the sum of the player's scores, 0 for a
  player with no scores.
- `get_top_scores(n)` returns the `n` highest scores on the whole board,
  highest first, over all players. If fewer than `n` scores have been
  recorded, all of them are returned; an empty board gives `[]`. A score
  recorded twice appears twice. `n` must be an `int` of 1 or more, or
  `ValueError` is raised.

When `record_score` has several problems, `KeyError` for an unknown player is
raised before `ValueError` for the score.

A failed call has no effect: if a method raises, every player's scores are
unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_player`, `bool` scores,
what happens if a returned list is changed, the text of error messages,
saving the board to a file, and use from several threads.
