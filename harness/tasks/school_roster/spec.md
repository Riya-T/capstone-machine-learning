# School roster

Write a module `roster.py` that keeps track of which students are in which
grade of a school.

## Interface

```python
class RosterError(Exception): ...


class Roster:
    def __init__(self): ...
    def add_student(self, name: str, grade: int) -> None: ...
    def get_grade(self, name: str) -> int: ...
    def get_students(self, grade: int) -> list[str]: ...
    def get_all_students(self) -> list[str]: ...
    def get_grades(self) -> list[int]: ...
```

Grades are the `int`s 1 to 12. A student is identified by name, and a name
is a non-empty `str`.

## Adding students

- `add_student(name, grade)` puts a new student in a grade. A name that is
  not a non-empty `str`, or a grade that is not an `int` from 1 to 12,
  raises `ValueError`. A name that is already on the roster raises
  `RosterError`, whatever grade it is in. When several problems apply, the
  `ValueError` is raised.
- `get_grade(name)` returns the student's grade. It raises `KeyError` for a
  name that is not on the roster, including values that are not strings at
  all, such as `None` or `7`.

## Listing students

- `get_students(grade)` returns the names of the students in that grade, in
  the order they were added. A grade with no students gives `[]`. A grade
  that is not an `int` from 1 to 12 raises `ValueError`.
- `get_all_students()` returns every name on the roster, lowest grade
  first; within a grade, in the order the students were added.
- `get_grades()` returns the grades that have at least one student, lowest
  first.

A failed call has no effect: if a method raises, the roster is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` grades, what happens if a returned list is changed, the
text of error messages, saving the roster to a file, and use from several
threads.
