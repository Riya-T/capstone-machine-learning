# Course enrollment

Write a module `enrollment.py` that stores course and student records and
tracks which students are enrolled in each course.

## Interface

```python
class Course:
    course_code: str
    title: str
    capacity: int
    enrolled_students: set[str]


class EnrollmentSystem:
    def __init__(self): ...
    def add_course(self, course_code: str, title: str, capacity: int) -> None: ...
    def register_student(self, student_id: str) -> None: ...
    def enroll(self, student_id: str, course_code: str) -> bool: ...
```

## Courses and students

- `add_course` creates a course with the given code, title, and capacity.
  Adding a course with an existing code replaces its course record.
- `register_student` registers the student. Registering the same id again has
  no additional effect.
- A capacity is a non-negative integer. A negative capacity raises
  `ValueError` without changing the system.

## Enrollment

- `enroll` returns `False` if the student is not registered, the course does
  not exist, the student is already enrolled in that course, or the course
  has reached capacity.
- A successful enrollment adds the student to the course and returns `True`.
- Failed enrollment attempts do not change course membership or capacity.
- Capacity is independent for each course; a student may enroll in multiple
  courses.

## Unspecified behavior

Behavior not described here is unspecified. This includes identifier and
title validation, ordering of students, whether callers may modify public
attributes, and thread safety.
