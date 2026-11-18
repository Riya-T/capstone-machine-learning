# Cargo holds

Write a module `ship.py` that keeps track of the crates in a cargo ship's
holds: how many crates of each cargo type are in each hold, as crates are
loaded, unloaded and shifted from one hold to another.

## Interface

```python
class CargoError(Exception): ...


class NotEnoughCrates(CargoError): ...


class Ship:
    def __init__(self): ...
    def add_hold(self, name: str) -> None: ...
    def load(self, hold: str, cargo: str, count: int) -> None: ...
    def unload(self, hold: str, cargo: str, count: int) -> None: ...
    def shift_all(self, from_hold: str, to_hold: str) -> int: ...
    def seal_hold(self, name: str, into: str) -> int: ...
    def get_count(self, hold: str, cargo: str) -> int: ...
    def get_cargo(self, hold: str) -> list[str]: ...
    def get_holds(self) -> list[str]: ...
```

Hold names and cargo types are non-empty strings, and counts are `int`.

## Holds

- `add_hold(name)` adds an empty hold. A name that is already in use raises
  `CargoError`.
- `get_holds()` returns the names of the holds in use, in the order they
  were added.
- Every other method raises `KeyError` when given a hold name that is not in
  use: one that was never added, or one that was sealed.

## Crates

- `load(hold, cargo, count)` puts `count` crates of `cargo` into the hold.
  The count must be greater than 0; otherwise `ValueError` is raised.
- `unload(hold, cargo, count)` takes `count` crates of `cargo` out of the
  hold. Unloading more crates of a cargo type than the hold has (including
  a cargo type it has none of) raises `NotEnoughCrates`.
- `shift_all(from_hold, to_hold)` moves every crate of every cargo type from
  `from_hold` to `to_hold`, where they are added to any crates of the same
  type already there, and returns how many crates it moved in total.
  Afterwards `from_hold` is empty but still in use. If `from_hold` is
  already empty, nothing changes and it returns 0.
- `seal_hold(name, into)` moves every crate of every cargo type from hold
  `name` into hold `into` (added to any crates of the same type already
  there), then removes hold `name`: it is no longer listed by
  `get_holds()`, and every method treats it as not in use. It returns how
  many crates it moved in total. The other holds keep their order.
- `shift_all` and `seal_hold` raise `ValueError` when both holds are the
  same.
- `get_count(hold, cargo)` returns how many crates of `cargo` are in the
  hold: 0 for a cargo type the hold has none of.
- `get_cargo(hold)` returns the cargo types that have at least one crate in
  the hold, in alphabetical order. A cargo type whose crates have all gone
  (by `unload`, `shift_all` or `seal_hold`) is no longer listed.

Python note: a `dict` must not gain or lose keys while a `for` loop runs over
it (Python raises `RuntimeError: dictionary changed size during
iteration`). In `shift_all` and `seal_hold`, a loop over a hold's crates
that deletes entries from that hold (directly or by calling `unload`) must
loop over a copy such as `list(crates.items())`.

## Errors

When a call has more than one problem (for example a hold that is not in
use and a count of 0), which of the errors it raises is unspecified.

A failed call has no effect: if a method raises, every count and the list of
holds are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type: counts that are not `int` (such as `1.5`,
`"3"`, `True` or `None`), and cargo types or hold names that are not
non-empty strings (such as `""`, `None` or `1`), wherever they are passed.
It also includes which error is raised when a call has several problems,
unloading a count of 0 or less, sealing a hold that is empty, adding a hold
under the name of a hold that was sealed, what happens if a
returned list is changed, the text of error messages, saving the ship to a
file, and use from several threads.
