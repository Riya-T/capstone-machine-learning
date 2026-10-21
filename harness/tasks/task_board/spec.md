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
- `get_task(task_id)` returns `(project, title, due_day, done)`, where
  `done` is `True` once the task is completed.
- `complete(task_id)` marks the task as done. Completing a task that is
  already done raises `BoardError`.
- `get_open_tasks(project)` returns the ids of the project's open tasks, in
  the order they joined the project (by being added to it or moved into it).

## The open-task limit

A project can have at most **5** open tasks at a time. Done tasks do not
count. Adding a task to a project that already has 5 open tasks, or moving
an open task into one, raises `BoardError`.

## Moving tasks

`move_task(task_id, project)` moves the task to another project, where it
joins at the end. Moving a task to the project it is already in raises
`ValueError`. Done tasks can be moved too, and do not count toward the
limit of the project they move into.

## Errors

When a call has several problems, the first of these is raised:

1. `KeyError` for a task that does not exist, then for a project that does
   not exist;
2. `ValueError` for an invalid title or due day, or a move to the same
   project;
3. `BoardError`.

A failed call has no effect: if a method raises, every project and every
task is unchanged, and no task id is used up.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes project names and titles that are not strings, `bool` days or ids,
what happens if a returned list is changed, the text of error messages,
saving the board to a file, and use from several threads.
