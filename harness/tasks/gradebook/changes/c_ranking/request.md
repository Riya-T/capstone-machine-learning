Add class rankings to `gradebook.py`.

- Add `Gradebook.get_ranking() -> list[str]`: every student, the one with
  the highest `get_total` first. Students with equal totals keep the order
  they were added in. With no students the list is empty.
- Add `Gradebook.get_rank(name) -> int`: the student's 1-based position in
  `get_ranking()`. Raises `KeyError` for a name that is not a student.
- Add `Gradebook.get_assignment_ranking(title) -> list[str]`: the students
  who have a recorded score for that assignment, the highest `get_score`
  first, with ties in the order the students were added. Students without
  a score for it are left out. Raises `KeyError` for a title that is not an
  assignment.
- Rankings describe the gradebook as it stands when they are called:
  recording or replacing a score, `mark_late` and `clear_late` all change
  what later calls return.

All existing behavior must keep working.
