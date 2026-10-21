# Course enrollment

Write a module `enrollment.py` that keeps track of courses, students, and
which students hold a seat in which course.

## Interface

```python
class EnrollmentError(Exception): ...


class CourseFull(EnrollmentError): ...


class Registrar:
    def __init__(self): ...
    def add_course(self, course_id: str, capacity: int) -> None: ...
    def add_student(self, student_id: str) -> None: ...
    def enroll(self, student_id: str, course_id: str) -> None: ...
    def get_roster(self, course_id: str) -> list[str]: ...
    def get_schedule(self, student_id: str) -> list[str]: ...
    def get_open_seats(self, course_id: str) -> int: ...
```

## Courses and students

- `add_course(course_id, capacity)` adds a course with `capacity` seats. An
  empty course id raises `ValueError`, and so does a capacity that is not an
  `int` greater than 0. Adding a course id that was already added raises
  `EnrollmentError`; a bad capacity is reported first.
- `add_student(student_id)` adds a student. An empty student id raises
  `ValueError`, and adding a student id that was already added raises
  `EnrollmentError`.
- Every other method raises `KeyError` when given a student or course that
  has not been added, including values that are not strings at all, such as
  `None` or `1`.

## Enrolling

- `enroll(student_id, course_id)` gives the student a seat in the course.
  A student may be enrolled in any number of courses.
- Enrolling a student in a course they are already enrolled in raises
  `EnrollmentError`.
- A course never has more students than seats: enrolling in a course with
  no open seat raises `CourseFull`.

When a call to `enroll` has several problems, the first of these is raised:

1. `KeyError` for a student that has not been added, then for a course that
   has not been added;
2. `EnrollmentError` for a student already enrolled in the course;
3. `CourseFull`.

## Looking things up

- `get_roster(course_id)` returns the ids of the students enrolled in the
  course, in the order they enrolled.
- `get_schedule(student_id)` returns the ids of the courses the student is
  enrolled in, in the order the student enrolled in them (which need not be
  the order the courses were added).
- `get_open_seats(course_id)` returns how many seats are still free: the
  capacity minus the number of students enrolled.

A failed call has no effect: if a method raises, every roster, schedule and
seat count is unchanged, and no course or student is added.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_course` or `add_student`,
`bool` capacities, a student id that is also a course id, what happens if a
returned list is changed, the text of error messages, saving the registrar
to a file, and use from several threads.
