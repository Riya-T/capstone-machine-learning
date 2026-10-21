"""Gradebook: the students, assignments and scores of one class.

Planted bug (initial version): a score of 0 is rejected as if it were
negative. The public checks only record positive scores, so only the hidden
initial tests catch it. Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from gradebook import Gradebook
    book = Gradebook()
    book.add_student("ana")
    book.add_assignment("quiz", 10)
    book.record_score("ana", "quiz", 7)
"""


class GradebookError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_points(points, max_points):
    if isinstance(points, bool) or not isinstance(points, int) or not 0 < points <= max_points:
        raise ValueError(f"points must be an int from 0 to {max_points}, got {points!r}")


class Gradebook:
    def __init__(self):
        self._max_points = {}  # title -> max points, in the order added
        self._scores = {}  # name -> {title: points}, in the order students were added

    def add_student(self, name):
        check_name(name, "student name")
        if name in self._scores:
            raise GradebookError(f"{name!r} is already a student")
        self._scores[name] = {}

    def add_assignment(self, title, max_points):
        check_name(title, "assignment title")
        if isinstance(max_points, bool) or not isinstance(max_points, int) or max_points <= 0:
            raise ValueError(f"max_points must be a positive int, got {max_points!r}")
        if title in self._max_points:
            raise GradebookError(f"{title!r} is already an assignment")
        self._max_points[title] = max_points

    def record_score(self, name, title, points):
        self._require_student(name)
        self._require_assignment(title)
        check_points(points, self._max_points[title])
        self._scores[name][title] = points

    def get_score(self, name, title):
        self._require_student(name)
        self._require_assignment(title)
        if title not in self._scores[name]:
            raise GradebookError(f"no score for {name!r} on {title!r}")
        return self._scores[name][title]

    def get_total(self, name):
        self._require_student(name)
        return sum(self._scores[name].values())

    def get_students(self):
        return list(self._scores)

    def get_assignments(self):
        return list(self._max_points)

    def _require_student(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._scores:
            raise KeyError(name)

    def _require_assignment(self, title):
        if not isinstance(title, str) or title not in self._max_points:
            raise KeyError(title)
