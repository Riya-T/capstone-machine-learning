# Pantry inventory

Write a module `pantry.py` that keeps track of the food in a pantry: how
much of each item there is, and by which day each batch must be used.

## Interface

```python
class PantryError(Exception): ...


class Pantry:
    def __init__(self): ...
    def add_item(self, name: str, quantity: int, use_by: int) -> None: ...
    def use_item(self, name: str, quantity: int) -> None: ...
    def get_quantity(self, name: str) -> int: ...
    def get_batches(self, name: str) -> list[tuple[int, int]]: ...
    def get_expiring_by(self, day: int) -> list[str]: ...
    def get_items(self) -> list[str]: ...
```

Days are numbered from 0 as `int`; `use_by` is the last day on which a batch
may still be used. Quantities are counts, as `int`.

## Adding

- `add_item(name, quantity, use_by)` puts a batch of `quantity` units of
  `name` into the pantry, to be used by day `use_by`. The first time a name
  is added it becomes an item of the pantry; every later call adds another
  batch to that item. Two batches with the same `use_by` are kept as
  separate batches.
- An empty name raises `ValueError`. The quantity must be an `int` greater
  than 0 and the use-by day an `int` that is 0 or more; anything else raises
  `ValueError`. The name is checked first, then the quantity, then the
  use-by day.
- `get_items()` returns the names of all items in the order they were first
  added. An item stays listed even when none of it is left.

## Using

- `use_item(name, quantity)` takes `quantity` units of `name` out of the
  pantry, from the batch with the earliest use-by day first; when a batch
  runs out, the next earliest is used. Batches with the same use-by day are
  used in the order they were added. The quantity must be an `int` greater
  than 0, or `ValueError` is raised. Taking more than the pantry holds
  raises `PantryError`.
- `get_quantity(name)` returns how many units of the item are in the
  pantry, over all of its batches.
- `get_batches(name)` returns the item's batches with something left in
  them, as `(use_by, quantity)` tuples, earliest use-by day first. Batches
  with the same day come in the order they were added.
- `get_expiring_by(day)` returns the names of all items with at least one
  batch whose use-by day is `day` or earlier, in the order the items were
  first added. The day must be an `int` that is 0 or more, or `ValueError`
  is raised.
- `use_item`, `get_quantity` and `get_batches` raise `KeyError` for a name
  that is not an item, including values that are not strings at all, such
  as `None` or `1`.

When a call has several problems, the first of these is raised:

1. `KeyError` for a name that is not an item;
2. `ValueError` for an invalid quantity;
3. `PantryError` for taking more than there is.

A failed call has no effect: if a method raises, every item and every batch
is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names that are not strings passed to `add_item`, `bool` quantities
and days, what happens if a returned list is changed, the text of error
messages, saving the pantry to a file, and use from several threads.
