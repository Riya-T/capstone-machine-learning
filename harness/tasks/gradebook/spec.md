# Gradebook

Write a module `gradebook.py` that keeps the students, the assignments and
the scores of one class.

## Interface

```python
class GradebookError(Exception): ...


class Gradebook:
    def __init__(self): ...
    def add_student(self, name: str) -> None: ...
    def add_assignment(self, title: str, max_points: int) -> None: ...
    def record_score(self, name: str, title: str, points: int) -> None: ...
    def get_score(self, name: str, title: str) -> int: ...
    def get_total(self, name: str) -> int: ...
    def get_students(self) -> list[str]: ...
    def get_assignments(self) -> list[str]: ...
```

All points are whole numbers, as `int`.

## Students and assignments

- `add_student(name)` adds a student. An empty name raises `ValueError`, and
  a name that is already a student raises `GradebookError`.
- `add_assignment(title, max_points)` adds an assignment worth up to
  `max_points`. An empty title raises `ValueError`; `max_points` must be an
  `int` greater than 0, or `ValueError` is raised; a title that is already
  an assignment raises `GradebookError`. The checks happen in that order.
- `get_students()` returns the names in the order they were added, and
  `get_assignments()` the titles in the order they were added.
- Every other method raises `KeyError` when given a name that is not a
  student or a title that is not an assignment, including values that are
  not strings at all, such as `None` or `1`. The name is checked before the
  title.

## Scores

- `record_score(name, title, points)` records the student's points for the
  assignment. `points` must be an `int` from 0 up to and including the
  assignment's `max_points`, or `ValueError` is raised. Recording a score
  for the same student and assignment again replaces the earlier score.
- `get_score(name, title)` returns the recorded points, and raises
  `GradebookError` when no score has been recorded for that student and
  assignment.
- `get_total(name)` returns the sum of the student's recorded scores.
  Assignments without a recorded score add nothing, so a new student's
  total is 0.

When a call has several problems, the first of these is raised:

1. `KeyError` for a name that is not a student;
2. `KeyError` for a title that is not an assignment;
3. `ValueError` for invalid points.

A failed call has no effect: if a method raises, every score and every
total is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names or titles that are not strings passed to `add_student` and
`add_assignment`, `bool` values for points, what happens if a returned list
is changed, the text of error messages, saving the gradebook to a file, and
use from several threads.
