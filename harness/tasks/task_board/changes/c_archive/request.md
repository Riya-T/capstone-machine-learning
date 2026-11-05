Let tasks in `board.py` be archived: taken off the board without being
deleted, and brought back later if needed.

- Add `Board.archive(task_id)`. The task leaves its project's open tasks
  and no longer counts toward the project's open-task limit. Open and done
  tasks can both be archived. Archiving a task that is already archived
  raises `BoardError`.
- Add `Board.restore(task_id)`, which puts an archived task back into the
  project it was archived from. A restored open task joins the end of the
  project's open tasks and counts toward its limit again; a restored done
  task stays done. Restoring a task that is not archived raises
  `BoardError`, and so does restoring an open task into a project that
  already has as many open tasks as its limit. Whether done tasks count
  toward the limit stays unspecified, so restoring a done task into such a
  project is unspecified too.
- Add `Board.is_archived(task_id) -> bool` and
  `Board.get_archived(project) -> list[int]`: the ids of the project's
  archived tasks, in the order they were archived.
- Like every method that takes a task id, `archive`, `restore` and
  `is_archived` raise `KeyError` for an id that `add_task` has not
  returned (`restore` too, not `BoardError`). `get_archived` raises
  `KeyError` for a name that is not a project.
- While a task is archived, `complete`, `move_task`, `rename_task` and
  `set_due_day` on it raise `BoardError` and change nothing. When such a
  call also has another problem (for example a project that does not
  exist, a wrong `expected_version`, or an invalid title or due day),
  which error is raised is unspecified. `get_task` and `get_version` still
  work on an archived task.
- Archiving and restoring each count as a change to the task: they add 1 to
  its version, and both take the keyword argument `expected_version=None`
  with the same meaning as for the other changes.
- Which error `archive` or `restore` raises when one call has several
  problems (for example a wrong `expected_version` for a task that is
  already archived) is unspecified.

All existing behavior must keep working.
