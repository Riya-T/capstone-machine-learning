Sort the items in `pantry.py` into categories such as "dairy" or "grains".

- `add_item` takes a new keyword argument `category=None`. For a name that
  is not yet an item, the category given becomes the item's category, and
  `None` means the category `"other"`. For an existing item, `None` keeps
  its current category and a string replaces it.
- An empty category raises `ValueError`, in `add_item` and in
  `set_category`, and so does `None` in `set_category`. When `add_item`
  raises, no item or batch is added and no category changes.
- Add `Pantry.set_category(name, category)`, which moves the item to the
  category, and `Pantry.get_category(name) -> str`. Both raise `KeyError`
  for a name that is not an item.
- Add `Pantry.get_categories() -> list[str]`: every category that currently
  holds at least one item, in the order of the first item in each category
  as listed by `get_items`.
- Add `Pantry.get_items_in(category) -> list[str]`: the names of the items
  in the category, in the order they were first added. A category with no
  items gives an empty list.
- Add `Pantry.get_category_quantity(category) -> int`: the sum of
  `get_quantity` over the items in the category, 0 when there are none.

All existing behavior must keep working.
