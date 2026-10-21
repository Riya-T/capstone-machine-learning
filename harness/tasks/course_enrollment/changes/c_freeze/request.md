Let the registrar freeze enrollment in a course in `enrollment.py`, for
example while the course is being moved to another room.

- Add `Registrar.freeze_course(course_id)`,
  `Registrar.unfreeze_course(course_id)` and
  `Registrar.is_frozen(course_id) -> bool`. All three raise `KeyError` for
  a course that has not been added. New courses are not frozen. Freezing a
  frozen course, or unfreezing one that is not frozen, does nothing.
- Add `class CourseFrozen(EnrollmentError)` to `enrollment.py`.
- While a course is frozen, enrolling anyone in it raises `CourseFrozen`
  and changes nothing. Students already enrolled keep their seats, and the
  course's roster and open seats can still be read.
- Only enrolling in the frozen course is blocked: other courses, and every
  other method, work as before.
- In `enroll`, `CourseFrozen` is checked after both `KeyError` checks and
  before every other check.

All existing behavior must keep working.
