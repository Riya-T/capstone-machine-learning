# Locker room

Write a module `lockers.py` that runs a room of lockers: items are put into
free lockers that are big enough, a fee is taken for each one, and items
are handed back later.

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

There are three sizes, from smallest to largest: `"small"`, `"medium"` and
`"large"`. An item fits into a locker of its own size or of any larger size.
Putting an item into a locker costs a fee that depends on the size of the
**locker** (not of the item), in whole cents:

| locker size | fee | holds items of size |
|---|---|---|
| `"small"` | 200 | `"small"` |
| `"medium"` | 300 | `"small"`, `"medium"` |
| `"large"` | 500 | `"small"`, `"medium"`, `"large"` |

So a small item put into a large locker costs 500, and a large item fits
only into a large locker.

Any other size, such as `"huge"`, `"Small"` or `None`, raises `ValueError`.

## Lockers

- `add_locker(locker_id, size)` adds an empty locker of that size. An empty
  id or an unknown size raises `ValueError`; adding an id that was already
  added raises `LockerError`. The `ValueError` checks come first.
- A locker is free while no item is in it. `get_free_lockers()` returns the
  ids of all lockers in the order they were added, keeping only the free
  ones. A locker freed by `retrieve` is back in its place in that order, not
  at the end.

## Items

Items and lockers have separate ids. `store`, `retrieve` and `get_locker`
take the id of an item, such as `"hat"`, and return the id of a locker,
such as `"S1"`. A locker id is not an item id: `get_locker("S1")` raises
`KeyError` unless an item called `"S1"` is in a locker.

- `store(item_id, size)` puts an item of that size into a free locker and
  returns the locker's id. The locker is chosen like this: the smallest
  locker size that fits the item and has a free locker; among the free
  lockers of that size, the one added first. The fee of the chosen locker
  is added to the takings.
- `store` raises, in this order: `ValueError` for an empty item id or an
  unknown size; `LockerError` when an item with that id is already in a
  locker; `NoLockerFree` when no free locker fits the item.
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
room.store("gloves", "small")  # "M1": both small lockers are taken, so the next size up
room.store("coat", "medium")   # "L1": the only free locker a medium item fits into
room.get_takings()             # 1300 (200 + 200 + 300 + 500: the fee of each locker)
room.get_locker("gloves")      # "M1"
room.retrieve("gloves")        # "M1"
room.retrieve("hat")           # "S1"
room.get_free_lockers()        # ["S1", "M1"]: in the order the lockers were added
room.get_takings()             # 1300: no fee is refunded
room.get_locker("hat")         # KeyError: "hat" is not in a locker any more
room.get_locker("S2")          # KeyError: "S2" is a locker, not an item
room.store("bag", "large")     # NoLockerFree: the only large locker is taken
room.store("hat", "medium")    # "M1": a retrieved item can be stored again
```

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_locker` or `store`, what
happens if a returned list is changed, the text of error messages, saving
the room to a file, and use from several threads.
