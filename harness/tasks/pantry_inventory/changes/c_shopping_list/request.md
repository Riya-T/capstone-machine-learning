Let `pantry.py` work out a shopping list from the amount of each item the
household wants to keep in stock.

- Add `Pantry.set_minimum(name, minimum)` and `Pantry.get_minimum(name) ->
  int`. Every item starts with a minimum of 0. The minimum must be an `int`
  that is 0 or more (not a `bool`). `set_minimum` raises `KeyError` for a
  name that is not an item, then `ValueError` for an invalid minimum, and
  changes nothing in either case. `get_minimum` raises `KeyError` for a name
  that is not an item.
- Add `Pantry.get_shopping_list(day=None) -> list[tuple[str, int]]`: one
  `(name, missing)` tuple for every item whose stock is below its minimum,
  where `missing` is the minimum minus the stock. Items come in the order
  they were first added; items with nothing missing are left out.
- Without `day`, the stock is `get_quantity(name)`. With `day`, only
  batches whose use-by day is `day` or later count as stock, so the list
  shows what to buy to still have enough on that day. `day` must be an
  `int` that is 0 or more (not a `bool`), or `ValueError` is raised.
- Adding a batch or using an item never changes its minimum.

All existing behavior must keep working.
