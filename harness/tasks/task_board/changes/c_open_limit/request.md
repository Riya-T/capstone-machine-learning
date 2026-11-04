Make the open-task limit in `board.py` adjustable. Some teams want a
stricter limit to keep focus, and some projects need more room.

- `Board` takes a new keyword argument `open_limit=5`: how many open tasks
  each project may have unless the project has its own limit. A limit
  below 1 raises `ValueError`.
- `add_project` takes a new keyword argument `open_limit=None`. `None` means
  the project uses the board's limit. A limit below 1 raises `ValueError`,
  and no project is added.
- Add `Board.get_open_limit(project) -> int`, which returns the project's
  current limit. It raises `KeyError` for a name that is not a project.
- Add `Board.set_open_limit(project, limit)`, which replaces the project's
  limit. It raises `KeyError` for a name that is not a project,
  `ValueError` for an invalid limit, and `BoardError` if the limit is
  valid but the project already has more open tasks than it. In each case
  nothing changes. A limit equal to the number of open tasks is fine.
- Adding a task to a project is refused with `BoardError` when that
  project already has as many open tasks as its own limit, and moving an
  open task out of a project frees a place in it, as with the fixed limit
  of 5.

For example, with `Board(open_limit=2)` and tasks 1 and 2 open in `"web"`,
`add_task("web", "blog", 1)` raises `BoardError`. After
`set_open_limit("web", 3)`, the same call returns 3, and
`set_open_limit("web", 2)` then raises `BoardError`, because `"web"` has 3
open tasks.

As before, whether done tasks count toward a limit, and moving a task into
a project that has reached its limit, are unspecified. So are limits that
are not `int`s, and which error is raised when `add_project` gets an
invalid limit together with another problem (for example a name that is
already a project), or `set_open_limit` gets several problems at once.
All existing behavior must keep working.
