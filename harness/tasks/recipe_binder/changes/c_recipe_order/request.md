Make the order in which `binder.py` lists a section's recipes adjustable,
because in some sections people look recipes up by name.

- `RecipeBinder` takes a new keyword argument `recipe_order="added"`. It
  must be `"added"` or `"name"`; anything else raises `ValueError`.
- Every section has a recipe order. `"root"` and every new section get the
  binder's `recipe_order`.
- Add `RecipeBinder.get_recipe_order(section) -> str` and
  `RecipeBinder.set_recipe_order(section, order)`, which replaces the
  section's recipe order. Both raise `KeyError` for a section that is not
  in use; `set_recipe_order` raises `ValueError` for an order other than
  `"added"` or `"name"`. In each case nothing changes. Which error is
  raised when both are wrong is unspecified.
- `get_recipes(section)` lists the section's recipes in its recipe order:
  - `"added"`: in the order they arrived there, earliest first, as before;
  - `"name"`: sorted by name, the way Python's `sorted` sorts strings.
- The setting only changes how `get_recipes` lists the recipes. Each
  section still remembers the order its recipes arrived in: after
  switching a section back to `"added"`, `get_recipes` lists them in that
  order again, and `delete_section` puts the deleted section's recipes at
  the end of its parent's in the order they arrived, whatever either
  section's setting.
- `set_recipe_order` changes no recipes, so a locked section's recipe
  order can be changed too.
- `undo` still puts back exactly the state from before the undone call:
  `set_recipe_order` is a call that `undo` reverses like any other, and an
  undone `delete_section` brings the section back with its recipe order.

All existing behavior must keep working.
