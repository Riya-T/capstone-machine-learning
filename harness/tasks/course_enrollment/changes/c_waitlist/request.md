Let students drop courses in `enrollment.py`, and let a full course keep a
waiting list, so that a seat given up goes to the first student in line.

- `enroll` takes a new keyword argument `waitlist=False`. When it is true
  and the course has no open seat, the student is put at the end of the
  course's waiting list instead of `CourseFull` being raised. When the
  course has an open seat, the student is enrolled as usual.
- A student on a waiting list is not enrolled in that course: it is not in
  their schedule, they are not on its roster, and they take no seat.
- `enroll` raises `EnrollmentError` for a student already on the course's
  waiting list, whether or not `waitlist` is true. This is checked together
  with the check for a student already enrolled.
- Joining a waiting list needs the course's prerequisites just like
  enrolling does: `MissingPrerequisite` is raised before the student would
  be put on the list.
- Add `Registrar.get_waitlist(course_id) -> list[str]`: the students
  waiting for the course, first in line first. It raises `KeyError` for a
  course that has not been added.
- Add `Registrar.drop(student_id, course_id)`:
  - A student enrolled in the course leaves it: they are taken off its
    roster and it is taken out of their schedule. If anyone is waiting, the
    first student in line is then enrolled at once: they leave the waiting
    list, are added at the end of the roster, and the course is added at
    the end of their schedule.
  - A student on the course's waiting list leaves the list, and nothing
    else changes.
  - Otherwise `drop` raises `EnrollmentError` and changes nothing. Before
    that, it raises `KeyError` for a student, then for a course, that has
    not been added.
  - Dropping never changes a student's completed courses.
- A student who dropped a course may enroll in it again later, like anyone
  else.

All existing behavior must keep working.
