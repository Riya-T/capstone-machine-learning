# Pantry inventory

Write a module `pantry.py` that keeps track of the food in a pantry: the
batches of each item, how much of each batch is left, and by which day each
batch must be used.

## Interface

```python
class Pantry:
    def __init__(self): ...
    def add_item(self, name: str, quantity: int, use_by: int) -> None: ...
    def use_item(self, name: str, quantity: int) -> None: ...
    def get_quantity(self, name: str) -> int: ...
    def get_batches(self, name: str) -> list[tuple[int, int]]: ...
    def get_expiring_by(self, day: int) -> list[tuple[str, int]]: ...
    def get_items(self) -> list[str]: ...
```

Days are numbered from 0 as `int`; `use_by` is the last day on which a batch
may still be used. Quantities are counts, as `int`.

## Adding

- `add_item(name, quantity, use_by)` puts a new batch of `quantity` units of
  `name` into the pantry, to be used by day `use_by`. The first time a name
  is added it becomes an item of the pantry; every later call adds another
  batch to that item, even one with the same `use_by` as an earlier batch.
- An empty name raises `ValueError`. The quantity must be an `int` greater
  than 0 and the use-by day an `int` that is 0 or more; anything else raises
  `ValueError`.
- `get_items()` returns the names of all items in the order they were first
  added.
- `get_batches(name)` returns the item's batches as `(use_by, quantity)`
  tuples, where `quantity` is how many units of that batch are left, in the
  order the batches were added, whatever their use-by days.
- `get_quantity(name)` returns how many units of the item are left, over all
  of its batches.

## Using

- `use_item(name, quantity)` takes `quantity` units of `name` out of the
  pantry, first in, first out: it takes as many as it can from the batch
  that was added first, then goes on to the next batch in the order added,
  and so on, until it has taken `quantity` units. The use-by days do not
  change this order.
- If the item has fewer than `quantity` units left, `use_item` takes all
  that is left. This is not an error.
- Whether `get_batches` still lists a batch that has no units left, as
  `(use_by, 0)`, is up to you: both are correct.
- The quantity must be an `int` greater than 0, or `ValueError` is raised.
- An item with nothing left is still an item: `get_items` still lists it,
  and `add_item` adds a new batch to it.

## Expiring

- `get_expiring_by(day)` tells how much of each item must be used by day
  `day`: the units left in the item's batches whose use-by day is `day` or
  earlier (`use_by <= day`), added up. It returns one `(name, units)` tuple
  for every item where this comes to more than 0, in the order the items
  were first added. Items where it is 0 are left out, whether no batch is
  due by `day` or the batches that are due have nothing left.
- The day must be an `int` that is 0 or more, or `ValueError` is raised.

## Example

```python
pantry = Pantry()
pantry.add_item("milk", 2, 10)
pantry.add_item("milk", 5, 4)
pantry.add_item("milk", 4, 7)
pantry.add_item("rice", 8, 30)
pantry.get_batches("milk")    # [(10, 2), (4, 5), (7, 4)]: in the order added
pantry.get_quantity("milk")   # 11
pantry.use_item("milk", 3)    # 2 units from the first batch, then 1 from the second
pantry.get_batches("milk")    # [(4, 4), (7, 4)], or [(10, 0), (4, 4), (7, 4)]
pantry.get_expiring_by(3)     # []
pantry.get_expiring_by(4)     # [("milk", 4)]: the day-4 batch counts on day 4 itself
pantry.get_expiring_by(10)    # [("milk", 8)]: 4 units of day 4 and 4 of day 7
pantry.use_item("milk", 6)    # the 4 units left of day 4, then 2 of day 7
pantry.get_batches("milk")    # [(7, 2)], or [(10, 0), (4, 0), (7, 2)]
pantry.get_expiring_by(4)     # []: the day-4 batch has nothing left
pantry.use_item("milk", 5)    # only 2 units are left, and both are taken
pantry.get_quantity("milk")   # 0
pantry.get_items()            # ["milk", "rice"]: milk is still an item
pantry.get_expiring_by(100)   # [("rice", 8)]: milk has nothing left
pantry.add_item("milk", 1, 12)
pantry.get_batches("milk")    # [(12, 1)], or [(10, 0), (4, 0), (7, 0), (12, 1)]
```

## Errors

- `use_item`, `get_quantity` and `get_batches` raise `KeyError` for a name
  that is not an item, including values that are not strings at all, such
  as `None` or `1`.
- A failed call has no effect: if a method raises, every item and every
  batch is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes whether a batch with no units left is still listed, names that are
not strings passed to `add_item`, `bool` quantities and days, which error
`use_item` raises when both its name and its quantity are wrong, what
happens if a returned list is changed, the text of error messages, saving
the pantry to a file, and use from several threads.
