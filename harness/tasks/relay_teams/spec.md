# Relay teams

Write a module `relay.py` that keeps track of the teams at a relay meet:
which runners are in each team's lineup, in running order, as runners are
added, removed and moved, and teams are merged or withdrawn.

## Interface

```python
class RelayError(Exception): ...


class RelayMeet:
    def __init__(self): ...
    def add_team(self, name: str) -> None: ...
    def add_runner(self, team: str, runner: str) -> None: ...
    def remove_runner(self, runner: str) -> None: ...
    def move_runner(self, runner: str, team: str) -> None: ...
    def merge_teams(self, source: str, into: str) -> int: ...
    def withdraw_team(self, name: str) -> int: ...
    def get_lineup(self, team: str) -> list[str]: ...
    def get_teams(self) -> list[str]: ...
```

Team names and runner names are non-empty strings.

## Teams

- `add_team(name)` adds a team with an empty lineup. A name that is already
  in use raises `RelayError`.
- `get_teams()` returns the names of the teams in use, in the order they
  were added.
- Every method that takes a team name raises `KeyError` when given a team
  that is not in use: one that was never added, or one that was merged into
  another team or withdrawn.

## Runners

- `add_runner(team, runner)` adds the runner at the end of the team's
  lineup.
- `remove_runner(runner)` takes the runner out of their team's lineup; the
  other runners keep their order. A runner who is not in any team raises
  `KeyError`.
- `move_runner(runner, team)` takes the runner out of their team and adds
  them at the end of `team`'s lineup. It raises `KeyError` if the runner is
  not in any team, and `ValueError` if the runner is already in `team`.
- `merge_teams(source, into)` moves every runner of team `source`, in
  running order, to the end of team `into`'s lineup, then removes team
  `source`: it is no longer listed by `get_teams()`, and every method
  treats it as not in use. It returns how many runners it moved (0 if the
  lineup was empty). The other teams keep their order. It raises
  `ValueError` when both teams are the same.
- `withdraw_team(name)` removes team `name` together with every runner in
  its lineup: the team is no longer listed by `get_teams()`, every method
  treats it as not in use, and its runners are in no team. It returns how
  many runners it removed.
- `get_lineup(team)` returns the runners of the team in running order: the
  order they were added, changed only by the calls above.

Python note: a `list` must not lose items while a `for` loop runs over it
(Python then skips items without any error). A loop over a lineup that
takes runners out of that same lineup (directly or by calling
`move_runner` or `remove_runner`) must loop over a copy such as
`list(lineup)`.

Example:

```python
meet = RelayMeet()
meet.add_team("hawks")
meet.add_team("owls")
meet.add_runner("hawks", "ana"); meet.add_runner("hawks", "ben")
meet.add_runner("owls", "cy")
meet.move_runner("ana", "owls")    # hawks: ben   owls: cy, ana
meet.merge_teams("hawks", "owls")  # returns 1; owls: cy, ana, ben
meet.withdraw_team("owls")         # returns 3; no teams left
```

## Errors

When a call has more than one problem (for example a team that is not in
use and a runner who is not in any team), which of the errors it raises is
unspecified.

A failed call has no effect: if a method raises, every lineup and the list
of teams are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type, such as team or runner names that are
not non-empty strings (`""`, `None` or `1`), wherever they are passed. It
also includes which error is raised when a call has several problems,
adding a runner who is already in a team (this one or another), adding a
runner again after they were removed or their team was withdrawn, adding a
team under the name of a team that was merged or withdrawn, what
happens if a returned list is changed, the text of error messages, saving
the meet to a file, and use from several threads.
