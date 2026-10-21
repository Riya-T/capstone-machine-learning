"""Task board with queries for overdue tasks and tasks due on a day.

Correct solution for task_board after c_overdue.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from board import Board
    board = Board()
    board.add_project("website")
    task_id = board.add_task("website", "write the landing page", 3)
    board.complete(task_id)
"""

OPEN_LIMIT = 5  # open tasks per project


class BoardError(Exception):
    pass


def check_title(title):
    if not isinstance(title, str) or not title:
        raise ValueError("title must be a non-empty str")


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day < 0:
        raise ValueError(f"day must be an int >= 0, got {day!r}")


class Board:
    def __init__(self):
        self._projects = {}  # project name -> open task ids in joining order
        self._tasks = {}  # task id -> {"project", "title", "due_day", "done"}
        self._next_id = 1

    def add_project(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._projects:
            raise BoardError(f"project {name!r} already exists")
        self._projects[name] = []

    def add_task(self, project, title, due_day):
        open_ids = self._project(project)
        check_title(title)
        check_day(due_day)
        if len(open_ids) >= OPEN_LIMIT:
            raise BoardError(f"project {project!r} already has {OPEN_LIMIT} open tasks")
        task_id = self._next_id
        self._next_id += 1
        self._tasks[task_id] = {
            "project": project,
            "title": title,
            "due_day": due_day,
            "done": False,
        }
        open_ids.append(task_id)
        return task_id

    def complete(self, task_id):
        task = self._task(task_id)
        if task["done"]:
            raise BoardError(f"task {task_id} is already done")
        task["done"] = True
        self._projects[task["project"]].remove(task_id)

    def move_task(self, task_id, project):
        task = self._task(task_id)
        target = self._project(project)
        if task["project"] == project:
            raise ValueError(f"task {task_id} is already in {project!r}")
        if not task["done"]:
            if len(target) >= OPEN_LIMIT:
                raise BoardError(f"project {project!r} already has {OPEN_LIMIT} open tasks")
            self._projects[task["project"]].remove(task_id)
            target.append(task_id)
        task["project"] = project

    def get_task(self, task_id):
        task = self._task(task_id)
        return (task["project"], task["title"], task["due_day"], task["done"])

    def get_open_tasks(self, project):
        return list(self._project(project))

    def get_projects(self):
        return list(self._projects)

    def get_overdue(self, today, project=None):
        candidates = self._open_task_ids(project)
        check_day(today)
        late = [i for i in candidates if self._tasks[i]["due_day"] < today]
        return sorted(late, key=lambda i: (self._tasks[i]["due_day"], i))

    def get_due_on(self, day, project=None):
        candidates = self._open_task_ids(project)
        check_day(day)
        return sorted(i for i in candidates if self._tasks[i]["due_day"] == day)

    def _open_task_ids(self, project):
        # None means every project; otherwise the name must be a project.
        if project is not None:
            self._project(project)
        return [
            task_id
            for task_id, task in self._tasks.items()
            if not task["done"] and (project is None or task["project"] == project)
        ]

    def _project(self, name):
        # Non-str names are never stored, so they count as "not a project" too.
        if not isinstance(name, str) or name not in self._projects:
            raise KeyError(name)
        return self._projects[name]

    def _task(self, task_id):
        if isinstance(task_id, bool) or not isinstance(task_id, int) or task_id not in self._tasks:
            raise KeyError(task_id)
        return self._tasks[task_id]
