Add an undo to `binder.py`, so a reorganization that went wrong can be
taken back.

- Add `RecipeBinder.undo() -> None`. It reverses the most recent
  successful call that has not been undone yet among `add_section`,
  `add_recipe`, `remove_recipe`, `move_section`, `delete_section`, and any
  other method that changes the sections or recipes, including methods
  added later. Each further `undo` goes one call further back.
- Undoing a call puts every section's recipes and subsections, in their
  order, back to exactly what they were just before that call. A call that
  changed several things is undone as a whole:
  - an undone `delete_section` brings the deleted section back at its old
    position among its parent's subsections, with its recipes and
    subsections in their old order, and takes those recipes and
    subsections away from the parent again; its name is in use again;
  - an undone `move_section` puts the section back under its old parent,
    at its old position, with everything below it;
  - an undone `remove_recipe` puts the recipe back at its old position in
    its section, and it is in the binder again;
  - an undone `add_section` removes the section, and its name may then be
    added again; an undone `add_recipe` removes the recipe;
  - `get_section_of` follows: every recipe is reported in the section that
    held it before the undone call.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `BinderError` and changes
  nothing. The `"root"` section is never undone: it is there from the
  start.

All existing behavior must keep working.
