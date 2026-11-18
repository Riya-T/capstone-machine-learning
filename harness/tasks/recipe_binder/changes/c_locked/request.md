Let sections in `binder.py` be locked, so a finished section's recipes
can't be changed by accident.

- Add `class SectionLocked(BinderError)` to `binder.py`.
- Add `RecipeBinder.set_locked(section, locked)` and
  `RecipeBinder.get_locked(section) -> bool`. Both raise `KeyError` for a
  section that is not in use. `locked` is `True` (lock the section) or
  `False` (unlock it). Every section starts unlocked, including `"root"`.
- A locked section's recipes can't change. These calls raise
  `SectionLocked` and change nothing:
  - `add_recipe` into a locked section;
  - `remove_recipe` of a recipe in a locked section;
  - `delete_section` of a section that is locked, or whose parent is
    locked (its recipes would leave the one or arrive in the other);
  - any other method that adds recipes to a section or takes them out of
    one, including methods added later, when that section is locked.
- Locking does not affect sections: `add_section` and `move_section` work
  as before, also into, out of or on a locked section. Locking a section
  does not lock the sections below it.
- When a call would raise `SectionLocked` and also has another problem,
  which error is raised is unspecified.
- `undo` still puts back exactly the state from before the undone call:
  `set_locked` is a call that `undo` reverses like any other.
  `set_locked` changes no recipes or sections.

All existing behavior must keep working.
