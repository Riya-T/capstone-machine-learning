# Team roster

Write a module `roster.py` that manages a basketball team's roster under a
salary cap.

## Interface

```python
POSITIONS = ("PG", "SG", "SF", "PF", "C")


class RosterError(Exception): ...


class CapExceeded(RosterError): ...


class Roster:
    def __init__(self, salary_cap: int): ...
    def add_player(self, name: str, position: str, salary: int) -> None: ...
    def remove_player(self, name: str) -> None: ...
    def get_players(self, position: str | None = None) -> list[str]: ...
    def get_player(self, name: str) -> dict: ...
    def get_payroll(self) -> int: ...
    def get_cap_space(self) -> int: ...
```

`POSITIONS` is a module-level constant listing the five positions.

## The salary cap

`Roster(salary_cap)` starts an empty roster. The cap must be an `int`
greater than 0, or `ValueError` is raised.

`get_payroll()` is the total salary of every player on the roster, and
`get_cap_space()` is the salary cap minus `get_payroll()`. The payroll may reach the
cap exactly but never go over it.

## Players

`add_player(name, position, salary)` adds a player. When a call has several
problems, the first of these is raised:

1. `ValueError` if `name` is empty;
2. `ValueError` unless `position` is one of `POSITIONS` (exact spelling);
3. `ValueError` unless `salary` is an `int` greater than 0;
4. `RosterError` if a player with that name is already on the roster;
5. `CapExceeded` if adding the player would put the payroll over the cap.

`remove_player(name)` removes a player, and `get_player(name)` returns a `dict`
with the keys `name`, `position` and `salary`. Both raise `KeyError` for a
name that is not on the roster, including values that are not strings.

`get_players()` returns the names of every player, in the order they were
added. A player who was removed and then added again counts as added at
that later time. `get_players(position)` returns only the players at that
position, in the same order; a position that is not one of `POSITIONS`
raises `ValueError`.

A failed call has no effect: if a method raises, the roster is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_player`, `bool` values as
the cap or a salary, what happens if a returned dict or list is changed, the
text of error messages, extra keys in the dict from `get_player`,
and saving the roster to a file.
