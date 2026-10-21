"""Task board with an adjustable open-task limit per board and per project.

Correct solution for task_board after c_open_limit.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from board import Board
    board = Board(open_limit=3)
    board.add_project("website", open_limit=8)
    task_id = board.add_task("website", "write the landing page", 3)
    board.set_open_limit("website", 4)
"""

DEFAULT_OPEN_LIMIT = 5  # open tasks per project unless the board or project says otherwise


class BoardError(Exception):
    pass


def check_title(title):
    if not isinstance(title, str) or not title:
        raise ValueError("title must be a non-empty str")


def check_day(day):
    if isinstance(day, bool) or not isinstance(day, int) or day < 0:
        raise ValueError(f"day must be an int >= 0, got {day!r}")


def check_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError(f"open limit must be an int >= 1, got {limit!r}")


class Board:
    def __init__(self, open_limit=DEFAULT_OPEN_LIMIT):
        check_limit(open_limit)
        self._open_limit = open_limit
        # project name -> {"open": task ids in joining order, "limit": int}
        self._projects = {}
        self._tasks = {}  # task id -> {"project", "title", "due_day", "done"}
        self._next_id = 1

    def add_project(self, name, open_limit=None):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if open_limit is None:
            open_limit = self._open_limit
        check_limit(open_limit)
        if name in self._projects:
            raise BoardError(f"project {name!r} already exists")
        self._projects[name] = {"open": [], "limit": open_limit}

    def add_task(self, project, title, due_day):
        target = self._project(project)
        check_title(title)
        check_day(due_day)
        self._require_room(project)
        task_id = self._next_id
        self._next_id += 1
        self._tasks[task_id] = {
            "project": project,
            "title": title,
            "due_day": due_day,
            "done": False,
        }
        target["open"].append(task_id)
        return task_id

    def complete(self, task_id):
        task = self._task(task_id)
        if task["done"]:
            raise BoardError(f"task {task_id} is already done")
        task["done"] = True
        self._projects[task["project"]]["open"].remove(task_id)

    def move_task(self, task_id, project):
        task = self._task(task_id)
        target = self._project(project)
        if task["project"] == project:
            raise ValueError(f"task {task_id} is already in {project!r}")
        if not task["done"]:
            self._require_room(project)
            self._projects[task["project"]]["open"].remove(task_id)
            target["open"].append(task_id)
        task["project"] = project

    def get_task(self, task_id):
        task = self._task(task_id)
        return (task["project"], task["title"], task["due_day"], task["done"])

    def get_open_tasks(self, project):
        return list(self._project(project)["open"])

    def get_projects(self):
        return list(self._projects)

    def get_open_limit(self, project):
        return self._project(project)["limit"]

    def set_open_limit(self, project, limit):
        target = self._project(project)
        check_limit(limit)
        if len(target["open"]) > limit:
            raise BoardError(f"project {project!r} has more than {limit} open tasks")
        target["limit"] = limit

    def _require_room(self, project):
        target = self._projects[project]
        if len(target["open"]) >= target["limit"]:
            raise BoardError(f"project {project!r} already has {target['limit']} open tasks")

    def _project(self, name):
        # Non-str names are never stored, so they count as "not a project" too.
        if not isinstance(name, str) or name not in self._projects:
            raise KeyError(name)
        return self._projects[name]

    def _task(self, task_id):
        if isinstance(task_id, bool) or not isinstance(task_id, int) or task_id not in self._tasks:
            raise KeyError(task_id)
        return self._tasks[task_id]
