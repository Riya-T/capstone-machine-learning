Sort the batches in `cooler.py` into categories, such as `"roses"` or
`"greens"`, and let a category set the freshness losses of its batches.

- Add `FlowerCooler.add_category(name, daily_loss=None, late_loss=None)`.
  The name must be a non-empty `str`, or `ValueError` is raised. A loss of
  `None` means the category uses the cooler's value; any other value must
  be an `int` of 0 or more (not a `bool`), or `ValueError` is raised.
  Adding a name that was already added raises `CoolerError`, after every
  `ValueError` check. A failed call adds no category.
- Add `FlowerCooler.get_categories() -> list[str]`, the names in the order
  they were added.
- `add_batch` takes a new keyword argument `category=None`. `None` means
  the batch has no category. Otherwise the category must already have been
  added, or `KeyError` is raised. For `add_batch`, every `ValueError` comes
  first, then the `KeyError` for an unknown category, then the
  `CoolerError` for an id that is already in the cooler.
- Each of a batch's two losses is chosen on its own: the value given to
  `add_batch` (or later to `set_losses`) if there is one, otherwise its
  category's value if the category set one, otherwise the cooler's value.
  `get_losses` returns the losses chosen this way.
- Add `FlowerCooler.get_category(batch_id) -> str | None` (raises
  `KeyError` for a batch that is not in the cooler).
- `get_batches` and `get_wilted` take a new keyword argument
  `category=None`. `None` means every batch, as before; otherwise only the
  batches of that category are returned, still in the order they were
  added. A category that was never added raises `KeyError`; a category
  with no batches gives `[]`.

All existing behavior must keep working.
