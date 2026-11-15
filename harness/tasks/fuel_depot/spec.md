# Fuel depot

Write a module `depot.py` that keeps the fuel levels of the tanks in a depot
and a log of every movement of fuel.

## Interface

```python
class DepotError(Exception): ...


class NotEnoughFuel(DepotError): ...


class Depot:
    def __init__(self): ...
    def add_tank(self, tank_id: str) -> None: ...
    def fill(self, tank_id: str, litres: int) -> None: ...
    def drain(self, tank_id: str, litres: int) -> None: ...
    def pump(self, from_id: str, to_id: str, litres: int) -> None: ...
    def pump_down(self, from_id: str, to_id: str, keep: int) -> int: ...
    def retire_tank(self, from_id: str, to_id: str) -> int: ...
    def get_level(self, tank_id: str) -> int: ...
    def get_log(self, tank_id: str) -> list[tuple[str, int]]: ...
    def get_tanks(self) -> list[str]: ...
```

All amounts are whole litres, as `int`.

## Tanks

- `add_tank(tank_id)` adds an empty tank, with a level of 0 and an empty
  log. Adding an id that is already in use raises `DepotError`.
- `get_tanks()` returns the ids of the tanks in use, in the order they were
  added.
- Every other method raises `KeyError` when given an id that is not a tank
  in use: one that was never added, one that was retired, or a value that
  is not a string at all, such as `None` or `1`.

## Moving fuel

- `litres` must be greater than 0, and `keep` must be 0 or more; otherwise
  `ValueError` is raised.
- `fill` adds the litres to the tank. `drain` takes them out. `pump` moves
  them from `from_id` to `to_id`.
- A level never goes below 0: a `drain` or `pump` of more than the level
  raises `NotEnoughFuel`.
- `pump_down(from_id, to_id, keep)` moves every litre above `keep` from
  `from_id` to `to_id`, so `from_id` is left with `keep` litres. If its
  level is already `keep` or less, nothing moves. It returns the number of
  litres moved.
- `retire_tank(from_id, to_id)` moves the whole level of `from_id` to
  `to_id`, then retires `from_id`, even if it was empty: it leaves
  `get_tanks()` and is no longer a tank in use. It returns the number of
  litres moved. A retired id may be added again later, as a new empty tank.
- `pump`, `pump_down` and `retire_tank` raise `ValueError` when `from_id`
  and `to_id` are the same tank, even if nothing would move.
- `get_level(tank_id)` returns the current level.

When a call has several problems, `KeyError` (for an id that is not a tank
in use) and `ValueError` (for an invalid amount or the same tank on both
sides) come before `NotEnoughFuel`. Which of `KeyError` and `ValueError` is
raised when a call has both is unspecified.

## Log

`get_log(tank_id)` returns the tank's movements, oldest first, as
`(kind, litres)` tuples with a positive number of litres:

- `("fill", litres)` for a fill;
- `("drain", litres)` for a drain;
- `("out", litres)` on the sending tank and `("in", litres)` on the
  receiving tank for every movement between two tanks, whether it comes
  from `pump`, `pump_down` or `retire_tank`.

A movement of 0 litres (a `pump_down` with nothing above `keep`, or
retiring an empty tank) adds nothing to any log.

A failed call has no effect: if a method raises, every level, every log and
the list of tanks are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes amounts that are not an `int` (such as `1.5`, `"3"`, `None` or a
`bool`), ids passed to `add_tank` that are empty or not strings, which of
`KeyError` and `ValueError` is raised when a call has both, what happens if
a returned list is changed, the text of error messages, saving the depot to
a file, and use from several threads.
