# Locker room

Write a module `lockers.py` that runs a room of lockers: items are put into
free lockers of their size, a fee is taken for each one, and items are
handed back later.

## Interface

```python
class LockerError(Exception): ...


class NoLockerFree(LockerError): ...


class LockerRoom:
    def __init__(self): ...
    def add_locker(self, locker_id: str, size: str) -> None: ...
    def store(self, item_id: str, size: str) -> str: ...
    def retrieve(self, item_id: str) -> str: ...
    def get_locker(self, item_id: str) -> str: ...
    def get_free_lockers(self) -> list[str]: ...
    def get_takings(self) -> int: ...
```

## Sizes and fees

There are three sizes: `"small"`, `"medium"` and `"large"`. Every locker
has one size, and an item goes only into a locker of its own size: a small
item into a small locker, a medium item into a medium locker, and a large
item into a large locker. Putting an item into a locker costs a fee that
depends on the size, in whole cents:

| size | fee |
|---|---|
| `"small"` | 200 |
| `"medium"` | 300 |
| `"large"` | 500 |

Any other size, such as `"huge"`, `"Small"` or `None`, raises `ValueError`.

## Lockers

- `add_locker(locker_id, size)` adds an empty locker of that size. It
  raises:
  - `ValueError` for an empty id or an unknown size;
  - `LockerError` for an id that was already added.
- A locker is free while no item is in it. `get_free_lockers()` returns the
  ids of all lockers in the order they were added, keeping only the free
  ones. A locker freed by `retrieve` is back in its place in that order, not
  at the end.

## Items

Items and lockers have separate ids. `store`, `retrieve` and `get_locker`
take the id of an item, such as `"hat"`, and return the id of a locker,
such as `"S1"`. A locker id is not an item id: `get_locker("S1")` raises
`KeyError` unless an item called `"S1"` is in a locker.

- `store(item_id, size)` puts an item of that size into a free locker of
  the same size and returns the locker's id. Of the free lockers of that
  size, it takes the one added first. The fee of that size is added to the
  takings. It raises:
  - `ValueError` for an empty item id or an unknown size;
  - `LockerError` when an item with that id is already in a locker;
  - `NoLockerFree` when no locker of that size is free, even if lockers of
    other sizes are.
- `retrieve(item_id)` takes the item out of its locker, which becomes free
  again, and returns the locker's id. No fee is refunded. Once retrieved,
  the item id can be stored again.
- `get_locker(item_id)` returns the id of the locker the item is in.
- `retrieve` and `get_locker` raise `KeyError` for an item that is not in a
  locker, including values that are not strings at all, such as `None` or
  `1`.
- `get_takings()` returns the total of all fees taken so far.

A failed call has no effect: if a method raises, every locker, every item
and the takings are unchanged.

## Example

```python
room = LockerRoom()
room.add_locker("S1", "small")
room.add_locker("S2", "small")
room.add_locker("M1", "medium")
room.add_locker("L1", "large")
room.store("hat", "small")     # "S1"
room.store("scarf", "small")   # "S2"
room.store("gloves", "small")  # NoLockerFree: both small lockers are taken
room.store("coat", "medium")   # "M1"
room.get_takings()             # 700 (200 + 200 + 300)
room.retrieve("hat")           # "S1"
room.get_free_lockers()        # ["S1", "L1"]: in the order the lockers were added
room.get_takings()             # 700: no fee is refunded
room.get_locker("hat")         # KeyError: "hat" is not in a locker any more
room.get_locker("S2")          # KeyError: "S2" is a locker, not an item
room.store("gloves", "small")  # "S1"
room.store("hat", "small")     # NoLockerFree
room.store("hat", "large")     # "L1": a retrieved item can be stored again
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when one call has several problems (for
example an unknown size and an id that was already added), ids that are not
strings passed to `add_locker` or `store`, what happens if a returned list
is changed, the text of error messages, saving the room to a file, and use
from several threads.
