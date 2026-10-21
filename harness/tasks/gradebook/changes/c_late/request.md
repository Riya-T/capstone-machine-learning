Let submissions in `gradebook.py` be flagged as late, so they earn only
partial credit.

- Add `Gradebook.mark_late(name, title)`, `Gradebook.clear_late(name, title)`
  and `Gradebook.is_late(name, title) -> bool`. All three raise `KeyError`
  for a name that is not a student (checked first) or a title that is not an
  assignment. A submission starts out not late. Marking a late submission
  late again, or clearing one that is not late, does nothing.
- The flag belongs to the student's submission for that assignment: it can
  be set before or after a score is recorded, and recording a score again
  does not change it.
- A late score counts for half, rounded down (`points // 2`), wherever
  scores are added up: in `get_total` and in every other value that is
  computed from the scores. `get_score` still returns the points exactly as
  recorded.
- Clearing the flag makes the full score count again.
- Marking or clearing never records a score: `get_score` for a submission
  without a score still raises `GradebookError`, and the student's total is
  unchanged until a score is recorded.

All existing behavior must keep working.
