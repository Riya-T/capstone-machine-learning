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

| locker size | fee |
|---|---|
| `"small"` | 200 |
| `"medium"` | 300 |
| `"large"` | 500 |

Any other size, such as `"huge"`, `"Small"` or `None`, raises `ValueError`.

## Lockers

- `add_locker(locker_id, size)` adds an empty locker of that size. An empty
  id or an unknown size raises `ValueError`; adding an id that was already
  added raises `LockerError`. The `ValueError` checks come first.
- A locker is free while no item is in it. `get_free_lockers()` returns the
  ids of the free lockers, in the order they were added.

## Items

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

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_locker` or `store`, what
happens if a returned list is changed, the text of error messages, saving
the room to a file, and use from several threads.
