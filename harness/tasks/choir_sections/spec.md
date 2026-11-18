# Choir sections

Write a module `choir.py` that keeps track of the singers of a choir: which
section each singer sings in, and the order the singers stand in within
their section.

## Interface

```python
class ChoirError(Exception): ...


class Choir:
    def __init__(self): ...
    def add_section(self, name: str) -> None: ...
    def add_singer(self, section: str, singer: str) -> None: ...
    def remove_singer(self, singer: str) -> None: ...
    def move_singer(self, singer: str, to_section: str) -> None: ...
    def move_all(self, source: str, into: str) -> int: ...
    def merge_sections(self, source: str, into: str) -> int: ...
    def get_singers(self, section: str) -> list[str]: ...
    def get_sections(self) -> list[str]: ...
```

Section names and singer names are non-empty strings.

## Sections

- `add_section(name)` adds an empty section. A section name that is
  already in use raises `ChoirError`.
- `get_sections()` returns the names of the sections in use, in the order
  they were added.
- Every other method that takes a section name raises `KeyError` when given
  a section that is not in use: one that was never added, or one that was
  merged into another.

## Singers

- A singer name is unique across the whole choir: no two singers, in the
  same section or in different sections, have the same name.
- `add_singer(section, singer)` adds a new singer at the end of the
  section. A singer name that is already in the choir, in any section,
  raises `ChoirError`.
- `remove_singer(singer)` takes the singer out of the choir. The singers
  behind them in their section keep their order.
- `move_singer(singer, to_section)` takes the singer out of their section
  and puts them at the end of `to_section`.
- `remove_singer` and `move_singer` raise `KeyError` for a singer who is not
  in the choir: one who was never added, or who was removed.
- `get_singers(section)` returns the singers of the section in the order
  they stand: the order in which they joined it (by `add_singer`,
  `move_singer`, `move_all` or `merge_sections`).

## Moving whole sections

- `move_all(source, into)` moves every singer of section `source` to the
  end of section `into`, keeping their order, and returns how many singers
  it moved. Afterwards `source` is empty but still in use. Moving from an
  empty section is not an error: nothing changes and it returns 0.
- `merge_sections(source, into)` moves every singer of section `source` to
  the end of section `into`, just like `move_all`, and then removes section
  `source`: it is no longer listed by `get_sections()` (the other sections
  keep their order), and every method treats it as not in use. It returns
  how many singers it moved (0 if `source` was empty; the section is still
  removed).
- `move_all` and `merge_sections` raise `ValueError` when both sections are
  the same.

Python note: a `list` or `dict` must not be changed while a `for` loop runs
over it (a `dict` raises `RuntimeError`, a `list` silently skips items). If
a loop over a section's singers moves or removes singers, loop over a copy
such as `list(singers)`.

## Errors

When a call has more than one problem (for example a section that is not in
use and a singer name that is taken), which of the errors it raises is
unspecified.

A failed call has no effect: if a method raises, the list of sections and
every section's singers in their order are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes:

- section or singer names that are not non-empty strings (such as `""`,
  `None` or `1`), wherever they are passed;
- moving a singer to the section they are already in;
- adding a singer again under the name of a removed singer, or a section
  under the name of a merged one;
- whether a singer may have the same name as a section;
- which error is raised when a call has several problems, what happens if a
  returned list is changed, the text of error messages, saving the choir to
  a file, and use from several threads.
