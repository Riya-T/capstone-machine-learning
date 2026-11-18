Let `groups.py` say where a student is, for example to call students up
group by group.

- Add `StudyGroups.find_student(student) -> tuple[str, int]`. It returns
  the name of the student's group and the student's position in that
  group, counting from 1 for the first member. A student who is not in any
  group raises `KeyError`.
- Add `StudyGroups.get_students() -> list[str]`. It returns every student
  who is in a group: the members of the first group of `get_groups()` in
  their order, then the members of the second group in their order, and so
  on.
- Both always reflect the current groups: after a `join`, `leave`,
  `swap_students` or `dissolve_group`, they report the new groups and
  positions.
- Neither of them changes anything.

All existing behavior must keep working.
