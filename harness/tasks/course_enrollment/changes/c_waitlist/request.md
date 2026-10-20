Add a FIFO waitlist to each course.

- When a registered student attempts to enroll in a course that is at
  capacity, add that student to the course's `waitlist` and return `False`.
- A successful enrollment still returns `True` and adds the student to
  `enrolled_students`.
- A student already enrolled or already on that course's waitlist cannot be
  added again; the repeat attempt returns `False` and preserves the queue.
- Unknown students and courses return `False` without changing a waitlist.
- `waitlist` is ordered by the time students first requested a place.
- There is no drop or promotion operation in this change; waitlist entries
  remain queued until a later feature handles them.

All existing behavior must keep working.
