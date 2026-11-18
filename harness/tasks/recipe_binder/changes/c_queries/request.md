Add two ways to look through the whole tree in `binder.py`.

- Add `RecipeBinder.get_all_recipes(section) -> list[str]`. It returns the
  recipes of `section` and of every section below it, in this order: first
  the section's own recipes (in the order of `get_recipes`), then, for each
  subsection in the order of `get_subsections`, everything
  `get_all_recipes` returns for that subsection. So a whole branch is
  listed before the next sibling's.
- Add `RecipeBinder.get_path(section) -> list[str]`. It returns the names
  of the sections from `"root"` down to `section`, both included:
  `get_path("root")` is `["root"]`, and `get_path(name)` for a section
  directly in `"root"` is `["root", name]`.
- Both raise `KeyError` for a section that is not in use, and neither
  changes anything.

All existing behavior must keep working.
