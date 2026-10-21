Let a course in `enrollment.py` require other courses to be completed
before a student may enroll in it.

- `add_course` takes a new keyword argument `prerequisites=()`: a list or
  tuple of course ids. Each one must be a course that was already added;
  otherwise `KeyError` is raised and the course is not added. This check
  comes after every existing check of `add_course`.
- Add `Registrar.record_completion(student_id, course_id)`, which records
  that the student has passed the course, for example in an earlier term.
  The student does not have to be enrolled in it, and recording a
  completion changes no roster, schedule or seat count. It raises
  `KeyError` for a student, then for a course, that has not been added.
  Recording the same course twice for a student does nothing.
- Add `Registrar.get_completed(student_id) -> list[str]`: the courses
  recorded for the student, in the order they were first recorded. It
  raises `KeyError` for a student that has not been added.
- Add `class MissingPrerequisite(EnrollmentError)` to `enrollment.py`.
- `enroll` raises `MissingPrerequisite` and changes nothing unless the
  student has completed every prerequisite of the course. This is checked
  after the check for a student already enrolled and before `CourseFull`.
- A course added without prerequisites can be joined by any student, as
  before.

All existing behavior must keep working.
