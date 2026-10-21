"""Gradebook with late flags and class rankings.

Planted bug (after c_late and c_ranking): rankings were added correctly,
but while reworking score lookups get_score was made to return 0 for a
submission without a score instead of raising GradebookError.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from gradebook import Gradebook
    book = Gradebook()
    book.add_student("ana")
    book.add_assignment("quiz", 10)
    book.record_score("ana", "quiz", 7)
    book.get_ranking()
"""


class GradebookError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_points(points, max_points):
    if isinstance(points, bool) or not isinstance(points, int) or not 0 <= points <= max_points:
        raise ValueError(f"points must be an int from 0 to {max_points}, got {points!r}")


class Gradebook:
    def __init__(self):
        self._max_points = {}  # title -> max points, in the order added
        self._scores = {}  # name -> {title: points}, in the order students were added
        self._late = {}  # name -> set of titles flagged late

    def add_student(self, name):
        check_name(name, "student name")
        if name in self._scores:
            raise GradebookError(f"{name!r} is already a student")
        self._scores[name] = {}
        self._late[name] = set()

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
        return self._scores[name].get(title, 0)

    def get_total(self, name):
        self._require_student(name)
        return sum(self._counted(name, title) for title in self._scores[name])

    def get_students(self):
        return list(self._scores)

    def get_assignments(self):
        return list(self._max_points)

    def mark_late(self, name, title):
        self._require_student(name)
        self._require_assignment(title)
        self._late[name].add(title)

    def clear_late(self, name, title):
        self._require_student(name)
        self._require_assignment(title)
        self._late[name].discard(title)

    def is_late(self, name, title):
        self._require_student(name)
        self._require_assignment(title)
        return title in self._late[name]

    def get_ranking(self):
        # sorted() is stable, so equal totals keep the order students were added.
        return sorted(self._scores, key=lambda name: -self.get_total(name))

    def get_rank(self, name):
        self._require_student(name)
        return self.get_ranking().index(name) + 1

    def get_assignment_ranking(self, title):
        self._require_assignment(title)
        scored = [name for name in self._scores if title in self._scores[name]]
        return sorted(scored, key=lambda name: -self._scores[name][title])

    def _counted(self, name, title):
        """The recorded points as they count toward the total."""
        points = self._scores[name][title]
        return points // 2 if title in self._late[name] else points

    def _require_student(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._scores:
            raise KeyError(name)

    def _require_assignment(self, title):
        if not isinstance(title, str) or title not in self._max_points:
            raise KeyError(title)
