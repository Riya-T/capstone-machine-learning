# Seed vault

Write a module `vault.py` that keeps track of a seed bank: how many packets
of each seed variety are kept in each drawer, as packets are deposited and
moved from one drawer to another.

## Interface

```python
class VaultError(Exception): ...


class NotEnoughSeeds(VaultError): ...


class SeedVault:
    def __init__(self): ...
    def add_drawer(self, name: str) -> None: ...
    def deposit(self, drawer: str, variety: str, count: int) -> None: ...
    def transfer(self, variety: str, from_drawer: str, to_drawer: str, count: int) -> None: ...
    def transfer_all(self, from_drawer: str, to_drawer: str) -> int: ...
    def retire_drawer(self, name: str, into: str) -> int: ...
    def get_count(self, drawer: str, variety: str) -> int: ...
    def get_drawers(self) -> list[str]: ...
```

Drawer names and varieties are non-empty strings, and counts are `int`.

## Drawers

- `add_drawer(name)` adds an empty drawer. A name that is already in use
  raises `VaultError`.
- `get_drawers()` returns the names of the drawers in use, in the order they
  were added.
- Every other method raises `KeyError` when given a drawer name that is not
  in use: one that was never added, or one that was retired.

## Packets

- `deposit(drawer, variety, count)` puts `count` packets of `variety` into
  the drawer. The count must be greater than 0; otherwise `ValueError` is
  raised.
- `transfer(variety, from_drawer, to_drawer, count)` moves `count` packets
  of `variety` from `from_drawer` to `to_drawer`. If `from_drawer` has fewer
  than `count` packets of `variety` (or none at all), it raises
  `NotEnoughSeeds`.
- `transfer_all(from_drawer, to_drawer)` moves every packet of every variety
  from `from_drawer` to `to_drawer` and returns how many packets it moved in
  total. Afterwards `from_drawer` is empty but still in use. Moving from an
  empty drawer is not an error: nothing changes and it returns 0.
- `retire_drawer(name, into)` moves every packet of every variety from
  drawer `name` to drawer `into`, just like `transfer_all`, and then removes
  drawer `name`: it is no longer listed by `get_drawers()` (the other drawers
  keep their order), and every method treats it as not in use. It returns
  how many packets it moved in total. Retiring an empty drawer is not an
  error: it returns 0 and the drawer is still removed.
- `get_count(drawer, variety)` returns how many packets of `variety` are in
  the drawer: 0 for a variety that has never been there, or whose packets
  have all left.

Python note: a `dict` must not gain or lose keys while a `for` loop runs
over it (Python raises `RuntimeError`). If `transfer_all` or
`retire_drawer` loops over a drawer's packets and something in the loop
(for example a call to `transfer`) can add or remove entries, loop over a
copy such as `list(packets.items())`.

## Errors

When a call has more than one problem (for example a drawer that is not in
use and a count of 0), which of the errors it raises is unspecified.

A failed call has no effect: if a method raises, every count and the list
of drawers are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes:

- values of the wrong type: counts that are not `int` (such as `1.5`, `"3"`,
  `True` or `None`), and varieties or drawer names that are not non-empty
  strings (such as `""`, `None` or `1`), wherever they are passed;
- a `transfer` with a count of 0 or less;
- `transfer`, `transfer_all` or `retire_drawer` with the same drawer on both
  sides;
- adding a drawer again under the name of a retired one;
- which error is raised when a call has several problems, what happens if a
  returned list is changed, the text of error messages, saving the vault to
  a file, and use from several threads.
