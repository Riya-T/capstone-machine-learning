Let students be withdrawn from `roster.py`, and put back if they return.

- Add `Roster.withdraw_student(name)`. The student leaves their grade: they
  no longer appear in `get_students`, `get_all_students` or `get_grades`,
  and `get_grade(name)` raises `KeyError`. Withdrawing a name that is not on
  the roster, including one already withdrawn, raises `KeyError`.
- Add `Roster.get_withdrawn() -> list[str]`: the names currently withdrawn,
  in the order they were withdrawn.
- Add `Roster.reinstate_student(name)`, which returns a withdrawn student to
  the grade they left, at the end of that grade's order, and removes the
  name from `get_withdrawn()`. A name that is not currently withdrawn raises
  `KeyError`.
- `add_student` with a withdrawn name is allowed: the student starts afresh
  in the grade given, and the name is removed from `get_withdrawn()`. The
  usual checks on the name and the grade still apply.

All existing behavior must keep working.
