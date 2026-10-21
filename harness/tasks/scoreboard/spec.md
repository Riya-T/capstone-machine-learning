# Scoreboard

Write a module `scoreboard.py` that keeps the score of one match between
any number of teams, built up from the scoring events of each team.

## Interface

```python
class ScoreboardError(Exception): ...


class Scoreboard:
    def __init__(self): ...
    def add_team(self, name: str) -> None: ...
    def score(self, team: str, kind: str) -> None: ...
    def get_score(self, team: str) -> int: ...
    def get_events(self, team: str) -> list[tuple[str, int]]: ...
    def get_standings(self) -> list[str]: ...
    def get_teams(self) -> list[str]: ...
```

All points are whole numbers, as `int`.

## Teams

- `add_team(name)` adds a team with a score of 0 and no events. An empty
  name raises `ValueError`, and a name that was already added raises
  `ScoreboardError`.
- `get_teams()` returns the names of all teams, in the order they were added.
- Every other method that takes a team raises `KeyError` for a name that
  was not added, including values that are not strings at all, such as
  `None` or `1`.

## Scoring

`score(team, kind)` records one scoring event for the team. The kind decides
how many points the event is worth:

| kind           | points |
|----------------|--------|
| `"try"`        | 5      |
| `"conversion"` | 2      |
| `"drop_goal"`  | 3      |

Any other kind raises `ValueError`: other words, other capitalization
(`"Try"`), the empty string, and values that are not strings at all. When
both the team and the kind are wrong, `KeyError` is raised.

- `get_score(team)` returns the sum of the points of all the team's events.
- `get_events(team)` returns the team's events, oldest first, as
  `(kind, points)` tuples, for example `[("try", 5), ("conversion", 2)]`.
- `get_standings()` returns the names of all teams, highest score first.
  Teams with equal scores stay in the order they were added. Teams without
  any events are included, with a score of 0.

A failed call has no effect: if a method raises, every score, every event
list and the standings are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_team`, what happens if a
returned list is changed, the text of error messages, saving the scoreboard
to a file, and use from several threads.
