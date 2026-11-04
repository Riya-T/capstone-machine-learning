# Task board

Write a module `board.py` that keeps the tasks of a small team's projects:
which project each task belongs to, when it is due and whether it is done.

## Interface

```python
class BoardError(Exception): ...


class Board:
    def __init__(self): ...
    def add_project(self, name: str) -> None: ...
    def add_task(self, project: str, title: str, due_day: int) -> int: ...
    def complete(self, task_id: int) -> None: ...
    def move_task(self, task_id: int, project: str) -> None: ...
    def get_task(self, task_id: int) -> tuple[str, str, int, bool]: ...
    def get_open_tasks(self, project: str) -> list[int]: ...
    def get_projects(self) -> list[str]: ...
```

Days are whole numbers, as `int`: day 0 is the day the board started.

## Projects

- `add_project(name)` adds a project with no tasks. An empty name raises
  `ValueError`, and adding a name that is already a project raises
  `BoardError`.
- `get_projects()` returns the names of all projects, in the order they
  were added.
- Every other method that takes a project raises `KeyError` for a name that
  is not a project, including values that are not strings at all, such as
  `None` or `1`.

## Tasks

- `add_task(project, title, due_day)` adds an open (not done) task to the
  project and returns its id: `1` for the first task added to the board,
  `2` for the next, and so on, over all projects. An empty title raises
  `ValueError`, and so does a `due_day` that is not an `int` of 0 or more.
- Every method that takes a `task_id` raises `KeyError` for an id that
  `add_task` has not returned, including values that are not `int`s at all,
  such as `None` or `"1"`.
- `get_task(task_id)` returns a tuple of four values: the name of the
  project the task is in now, its title, its due day, and `True` if it is
  done or `False` if it is open. For example, after
  `add_task("mobile", "login screen", 5)` returns 2, `get_task(2)` returns
  `("mobile", "login screen", 5, False)`.
- `complete(task_id)` marks the task as done. Completing a task that is
  already done raises `BoardError`.
- `get_open_tasks(project)` returns the ids of the project's open tasks, in
  the order they joined the project (by being added to it or moved into it).
  Done tasks are not listed.

## The open-task limit

A project is **full** when `get_open_tasks(project)` returns 5 ids. Done
tasks are not in that list, so they do not count, and completing a task
frees a place.

- `add_task` on a full project raises `BoardError`.
- Moving an open task into a full project raises `BoardError`, and the task
  stays where it was.
- A done task can move into any project, full or not.

For example, if tasks 1 to 5 are open in `"web"` and task 6 is open in
`"app"`:

- `add_task("web", "extra", 1)` and `move_task(6, "web")` raise
  `BoardError`;
- after `complete(2)`, `get_open_tasks("web")` returns `[1, 3, 4, 5]`, and
  `move_task(6, "web")` works: `get_open_tasks("web")` then returns
  `[1, 3, 4, 5, 6]`, and `"web"` is full again;
- the done task 2 can still move to `"app"`, and then back to the full
  `"web"`.

## Moving tasks

`move_task(task_id, project)` moves the task to another project. An open
task leaves the open tasks of its old project and is listed last in
`get_open_tasks` of the new one. Moving a task to the project it is already
in raises `ValueError`. Done tasks can be moved too: they stay done, and
`get_task` shows their new project.

## Errors

A failed call has no effect: if a method raises, every project and every
task is unchanged, and no task id is used up.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes which error is raised when a call has several problems (for
example a project that does not exist and an empty title, or a full project
and an invalid due day), project names and titles that are not strings,
`bool` days or ids, what happens if a returned list is changed, the text of
error messages, saving the board to a file, and use from several threads.
