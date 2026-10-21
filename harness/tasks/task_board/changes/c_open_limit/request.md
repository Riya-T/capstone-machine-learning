Make the open-task limit in `board.py` adjustable. Some teams want a
stricter limit to keep focus, and some projects need more room.

- `Board` takes a new keyword argument `open_limit=5`: how many open tasks
  each project may have unless the project has its own limit. It must be an
  `int` of at least 1 (not a `bool`); anything else raises `ValueError`.
- `add_project` takes a new keyword argument `open_limit=None`. `None` means
  the project uses the board's limit. Anything else must be an `int` of at
  least 1 (not a `bool`), or `ValueError` is raised and no project is added.
  If both the name and the limit are invalid, either `ValueError` may come
  first; both come before the `BoardError` for a name that is already a
  project.
- Add `Board.get_open_limit(project) -> int`, which returns the project's
  current limit. It raises `KeyError` for a name that is not a project.
- Add `Board.set_open_limit(project, limit)`, which replaces the project's
  limit. It raises `KeyError` for a name that is not a project, then
  `ValueError` for an invalid limit, then `BoardError` if the project
  already has more open tasks than the new limit. In each case nothing
  changes. A limit equal to the number of open tasks is fine.
- Adding a task to a project, or moving an open task into one, is refused
  with `BoardError` when that project already has as many open tasks as its
  own limit.

All existing behavior must keep working.
