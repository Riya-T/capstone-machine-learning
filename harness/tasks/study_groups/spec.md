# Study groups

Write a module `groups.py` that keeps track of the study groups in a class:
which students are in each group, in the order they joined, as students
join, leave, swap places and groups are dissolved.

## Interface

```python
class GroupError(Exception): ...


class StudyGroups:
    def __init__(self): ...
    def add_group(self, name: str) -> None: ...
    def join(self, student: str, group: str) -> None: ...
    def leave(self, student: str) -> None: ...
    def swap_students(self, a: str, b: str) -> None: ...
    def dissolve_group(self, name: str, into: str) -> int: ...
    def get_members(self, group: str) -> list[str]: ...
    def get_groups(self) -> list[str]: ...
```

Group names and student names are non-empty strings.

## Groups

- `add_group(name)` adds an empty group. A name that is already in use
  raises `GroupError`.
- `get_groups()` returns the names of the groups in use, in the order they
  were added.
- Every method that takes a group name raises `KeyError` when given a group
  that is not in use: one that was never added, or one that was dissolved.

## Students

- `join(student, group)` adds the student at the end of the group.
- `leave(student)` takes the student out of their group; the other members
  keep their order. A student who is not in any group raises `KeyError`.
- `swap_students(a, b)` makes two students of the same group change
  positions: `a` takes `b`'s position and `b` takes `a`'s. It raises
  `KeyError` if either student is not in any group, and `ValueError` if
  `a` and `b` are the same student.
- `dissolve_group(name, into)` moves every member of group `name`, in their
  order, to the end of group `into`, then removes group `name`: it is no
  longer listed by `get_groups()`, and every method treats it as not in
  use. It returns how many students it moved (0 if the group was empty).
  The other groups keep their order. It raises `ValueError` when both
  groups are the same.
- `get_members(group)` returns the students in the group, in order: the
  order they joined, changed only by the calls above.

Example:

```python
g = StudyGroups()
g.add_group("red")
g.add_group("blue")
g.join("ann", "red"); g.join("bob", "red"); g.join("cid", "blue")
g.swap_students("ann", "bob")    # red: bob, ann   blue: cid
g.dissolve_group("red", "blue")  # returns 2; blue: cid, bob, ann
g.get_groups()                   # ["blue"]
```

## Errors

When a call has more than one problem (for example a group that is not in
use and the same group twice), which of the errors it raises is
unspecified.

A failed call has no effect: if a method raises, every group's members and
the list of groups are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type, such as group or student names that are
not non-empty strings (`""`, `None` or `1`), wherever they are passed. It
also includes which error is raised when a call has several problems,
joining a student who is already in a group (this one or another),
swapping students who are in different groups, adding a group under the
name of a group that was dissolved, what happens
if a returned list is changed, the text of error messages, saving the
groups to a file, and use from several threads.
