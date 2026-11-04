Sort the items in `pantry.py` into categories such as "dairy" or "grains".

- `add_item` takes a new keyword argument `category=None`. When `add_item`
  creates a new item, the category given becomes the item's category, and
  `None` means the category `"other"`. When the name is already an item,
  `category` is ignored: the batch is added and the item keeps the
  category it has, whatever was passed. Only `set_category` moves an item.
- An empty category raises `ValueError` in `add_item` (for a new or an
  existing item) and in `set_category`, and so does `None` in
  `set_category`. When `add_item` raises, no item or batch is added.
- Add `Pantry.set_category(name, category)`, which moves the item to the
  category, and `Pantry.get_category(name) -> str`. Both raise `KeyError`
  for a name that is not an item.
- Add `Pantry.get_categories() -> list[str]`: every category that currently
  holds at least one item, in alphabetical order.
- Add `Pantry.get_items_in(category) -> list[str]`: the names of the items
  in the category, in alphabetical order. A category with no items gives
  an empty list.
- Add `Pantry.get_category_quantity(category) -> int`: the sum of
  `get_quantity` over the items in the category, 0 when there are none.

All existing behavior must keep working.
