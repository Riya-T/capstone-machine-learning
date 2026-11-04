# Task board

Write a module `board.py` that keeps the tasks of a small team's projects:
which project each task is in, its title, when it is due and whether it is
done.

## Interface

```python
class BoardError(Exception): ...


class Board:
    def __init__(self): ...
    def add_project(self, name: str) -> None: ...
    def add_task(self, project: str, title: str, due_day: int) -> int: ...
    def complete(self, task_id: int) -> None: ...
    def move_task(self, task_id: int, project: str) -> None: ...
    def get_task(self, task_id: int) -> tuple[str, int]: ...
    def get_open_tasks(self, project: str) -> list[int]: ...
    def get_projects(self) -> list[str]: ...
```

Days are whole numbers, as `int`: day 0 is the day the board started.

## Projects

- `add_project(name)` adds a project with no tasks. It raises:
  - `ValueError` for an empty name;
  - `BoardError` for a name that is already a project.
- `get_projects()` returns the names of all projects, in the order they
  were added.
- `add_task` and `get_open_tasks` raise `KeyError` for a name that is not a
  project, including values that are not strings at all, such as `None` or
  `1`.

## Tasks

- `add_task(project, title, due_day)` adds an open (not done) task to the
  project and returns its id: `1` for the first task added to the board,
  `2` for the next, and so on, over all projects. It raises:
  - `KeyError` for a project that does not exist;
  - `ValueError` for an empty title;
  - `ValueError` for a due day below 0;
  - `BoardError` when the project is full (see below).
- `get_task(task_id)` returns the task's title and due day, as a tuple,
  for open and done tasks alike. For example, after
  `add_task("mobile", "login screen", 5)` returns 2, `get_task(2)`
  returns `("login screen", 5)`.
- `complete(task_id)` marks an open task as done.
- `get_open_tasks(project)` returns the ids of the project's open tasks, in
  the order they joined the project (by being added to it or moved into
  it). Done tasks are not listed.
- Every method that takes a `task_id` raises `KeyError` for an id that
  `add_task` has not returned, including values that are not `int`s at all,
  such as `None` or `"1"`.

## Moving tasks

`move_task(task_id, project)` moves the task to another project. An open
task leaves the open tasks of its old project and is listed last in
`get_open_tasks` of the new one.

## Full projects

A project with 5 open tasks is **full**, and `add_task` on it raises
`BoardError`. Moving an open task out of a project frees a place in it.

For example, if tasks 1 to 5 are open in `"web"`:

- `add_task("web", "extra", 1)` raises `BoardError`;
- after `move_task(2, "app")`, `get_open_tasks("web")` returns
  `[1, 3, 4, 5]`, and `add_task("web", "extra", 1)` returns 6;
  `get_open_tasks("web")` then returns `[1, 3, 4, 5, 6]`, and `"web"` is
  full again.

## Errors

A failed call has no effect: if a method raises, every project and every
task is unchanged, and no task id is used up.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes:

- whether done tasks take up a place in their project, so whether a
  project with fewer than 5 open tasks but some done ones is full;
- moving a task into a full project, to the project it is already in, or
  to a project that does not exist;
- completing or moving a task that is already done;
- which error is raised when a call has several problems (for example a
  project that does not exist and an empty title);
- due days that are not `int`s, such as `1.5`, `"3"` or `None`, and `bool`
  days or ids;
- project names and titles that are not strings;
- what happens if a returned list is changed, the text of error messages,
  saving the board to a file, and use from several threads.
