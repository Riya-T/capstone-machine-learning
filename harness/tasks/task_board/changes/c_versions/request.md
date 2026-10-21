Several people now edit the same board in `board.py`, and one person's
change must not silently overwrite another's. Give every task a version
number so a stale edit can be detected.

- A new task has version 1. Every successful call that changes a task adds
  1 to that task's version. A call that raises leaves the version as it was.
- Add `Board.get_version(task_id) -> int`. It raises `KeyError` for a task
  that does not exist.
- Add `Board.rename_task(task_id, title)`, which replaces the task's title,
  and `Board.set_due_day(task_id, due_day)`, which replaces its due day. The
  new title and due day follow the same rules as in `add_task`, or
  `ValueError` is raised. Both work on open and done tasks, and both count
  as a change even when the new value equals the old one.
- `complete`, `move_task`, `rename_task` and `set_due_day` take a new
  keyword argument `expected_version=None`. When it is not `None` and is not
  the task's current version, the call raises `VersionConflict` and changes
  nothing. With `None`, no version check is made.
- Add `class VersionConflict(BoardError)` to `board.py`.
- `VersionConflict` is checked after every `KeyError` and before every other
  error.
- Adding a task to a project does not change the versions of the other
  tasks; moving a task changes only the version of the task that moved.

All existing behavior must keep working.
