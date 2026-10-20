Add optional prerequisites to courses.

- Extend `add_course` with an optional `prerequisite=None` course code.
- Add `mark_completed(student_id, course_code)`. It records completion only
  when the student is registered and the course exists; other calls do
  nothing.
- `enroll` returns `False` for a course with a prerequisite unless the
  student has completed that course. A failed prerequisite check must not
  enroll the student or add them to a waitlist.
- Courses without a prerequisite retain their existing enrollment behavior.
- A completed course need not be currently offered or have an open seat for
  its completion to satisfy the prerequisite.

All existing behavior must keep working.
