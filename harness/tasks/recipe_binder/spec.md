# Recipe binder

Write a module `binder.py` that keeps a binder of recipes organized in
sections. Sections can hold recipes and other sections, so the binder forms
a tree, and sections can be moved around or deleted.

## Interface

```python
class BinderError(Exception): ...


class RecipeBinder:
    def __init__(self): ...
    def add_section(self, name: str, parent: str) -> None: ...
    def add_recipe(self, section: str, recipe: str) -> None: ...
    def remove_recipe(self, recipe: str) -> None: ...
    def move_section(self, name: str, new_parent: str) -> None: ...
    def delete_section(self, name: str) -> None: ...
    def get_recipes(self, section: str) -> list[str]: ...
    def get_subsections(self, section: str) -> list[str]: ...
    def get_section_of(self, recipe: str) -> str: ...
```

Section names and recipe names are non-empty strings.

## Sections

- A new binder has one section, named `"root"`, with no recipes and no
  subsections. It has no parent, and it can never be moved or deleted.
- `add_section(name, parent)` adds an empty section as the last subsection
  of `parent`. A name that is already in use (including `"root"`) raises
  `BinderError`.
- `get_subsections(section)` returns the names of the sections directly
  inside `section`, in the order they arrived there (by `add_section`,
  `move_section` or `delete_section`), earliest first.
- Every method that takes a section name raises `KeyError` when given a
  name that is not in use: one that was never added, or one that was
  deleted.

## Recipes

- `add_recipe(section, recipe)` adds the recipe at the end of the
  section's recipes. Recipe names are unique in the whole binder: a recipe
  that is already in the binder (in any section) raises `BinderError`. A
  recipe that was removed may be added again.
- `remove_recipe(recipe)` removes the recipe from the binder. The other
  recipes of its section keep their order. A recipe that is not in the
  binder raises `KeyError`.
- `get_recipes(section)` returns the section's own recipes (not those of
  its subsections), in the order they arrived there (by `add_recipe` or
  `delete_section`), earliest first.
- `get_section_of(recipe)` returns the name of the section that holds the
  recipe. A recipe that is not in the binder raises `KeyError`.

## Moving and deleting sections

- `move_section(name, new_parent)` moves section `name`, with all its
  recipes and everything below it, so that it becomes the last subsection
  of `new_parent` (and is no longer a subsection of its old parent). It
  raises `BinderError` when `name` is `"root"`. `new_parent` is never
  `name` itself or a section below `name`: a call like that is
  unspecified.
- `delete_section(name)` removes section `name`, but keeps what it held:
  its recipes go to the end of its parent's recipes, in their order, and
  its subsections (each with everything below it) go to the end of its
  parent's subsections, in their order, and now have that parent as their
  parent. Deleting `"root"` raises `BinderError`.

## Errors

A failed call has no effect: if a method raises, every section's recipes
and subsections are unchanged. When a call has more than one problem,
which of its errors is raised is unspecified.

## Python notes

- Sections are looked up by name all the time, and records nested inside
  records (dicts in dicts, or objects that must be searched for) are easy
  to get wrong. A flat layout works well: for example a dict from each
  section name to the name of its parent, a dict from each section name to
  its list of subsection names, a dict from each section name to its list
  of recipes, and a dict from each recipe to its section. Put `"root"` in
  these in `__init__`, and make a new list for every new section.
- Create all of it in `__init__`, so that no two binders share anything (no
  class attributes, no default argument values).
- When a section is moved or deleted, update the parent of everything that
  moved as well as the lists of the old and the new parent. Do not change a
  list while looping over it: loop over a copy, such as
  `for x in list(items)`.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type (names that are not non-empty strings),
which error is raised when a call has several problems, moving a section
to the parent it already has, whether the name of a deleted section may be
added again, whether a recipe may have the same name as a section, what
happens if a returned list is changed, the text of error messages, saving
the binder to a file, and use from several threads.
