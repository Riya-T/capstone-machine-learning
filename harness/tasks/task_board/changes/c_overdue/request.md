Add queries to `board.py` that show which tasks need attention.

- Add `Board.get_overdue(today, project=None) -> list[int]`: the ids of the
  open tasks whose due day is before `today`. They are listed with the
  earliest due day first; tasks due on the same day are listed by id,
  smallest first. Done tasks are never listed.
- Add `Board.get_due_on(day, project=None) -> list[int]`: the ids of the
  open tasks due exactly on `day`, smallest id first.
- `today` and `day` must be an `int` of 0 or more (not a `bool`), or
  `ValueError` is raised.
- With `project=None` both queries cover every project. Given a project
  name, they cover only the tasks currently in that project, and raise
  `KeyError` for a name that is not a project. `KeyError` is checked before
  `ValueError`.

All existing behavior must keep working.
