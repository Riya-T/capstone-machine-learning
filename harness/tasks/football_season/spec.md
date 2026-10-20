# Football season

Write a module `season.py` that records the results of football games in a
season and ranks the teams.

## Interface

```python
class Season:
    def __init__(self): ...
    def add_team(self, name: str) -> None: ...
    def record_game(self, home: str, away: str, home_score: int, away_score: int) -> int: ...
    def get_record(self, team: str) -> dict: ...
    def get_standings(self) -> list[str]: ...
```

## Teams

`add_team(name)` adds a team to the season. An empty name, or a name that
was already added, raises `ValueError`.

## Games

`record_game(home, away, home_score, away_score)` records one finished game
and returns its id. Ids are integers that start at 1 and go up by 1 with
each recorded game. Two teams may play each other any number of times.

- A team that was not added raises `KeyError`, including values that are
  not strings.
- `home` and `away` being the same team raises `ValueError`.
- Each score must be an `int` that is 0 or more, or `ValueError` is raised.

`KeyError` is checked before either `ValueError`. A call that raises records
nothing and uses up no id.

## Records

`get_record(team)` returns a `dict` with these keys:

- `wins`, `losses`, `ties`: games the team won, lost and tied;
- `points_for`, `points_against`: points the team scored and allowed.

It raises `KeyError` for a team that was not added.

## Standings

`get_standings()` returns the names of every team, best first, ranked by:

1. standings points, highest first: 2 for each win and 1 for each tie;
2. then point differential, `points_for - points_against`, highest first;
3. then the order the teams were added, earlier first.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes team names that are not strings, `bool` values as scores, whether the returned dict has extra keys,
what happens if a returned dict or list is changed, and the text of error
messages.
