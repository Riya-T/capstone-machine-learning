"""Gradebook with totals that leave out a student's lowest scores.

Correct solution for gradebook after c_drop_lowest.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from gradebook import Gradebook
    book = Gradebook()
    book.add_student("ana")
    book.add_assignment("quiz", 10)
    book.record_score("ana", "quiz", 7)
    book.get_total_dropping("ana", 1)
"""


class GradebookError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_points(points, max_points):
    if isinstance(points, bool) or not isinstance(points, int) or not 0 <= points <= max_points:
        raise ValueError(f"points must be an int from 0 to {max_points}, got {points!r}")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError(f"count must be an int >= 0, got {count!r}")


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

    def get_total_dropping(self, name, count):
        self._require_student(name)
        check_count(count)
        dropped = set(self.get_dropped(name, count))
        return sum(points for title, points in self._counted_scores(name) if title not in dropped)

    def get_dropped(self, name, count):
        self._require_student(name)
        check_count(count)
        scores = self._counted_scores(name)
        # Stable sort: among equal scores the earlier-added assignment comes first.
        lowest = sorted(scores, key=lambda item: item[1])[:count]
        dropped = {title for title, _ in lowest}
        return [title for title, _ in scores if title in dropped]

    def _counted_scores(self, name):
        """(title, points) for every recorded score, in the order assignments were added."""
        recorded = self._scores[name]
        return [(title, recorded[title]) for title in self._max_points if title in recorded]

    def _require_student(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._scores:
            raise KeyError(name)

    def _require_assignment(self, title):
        if not isinstance(title, str) or title not in self._max_points:
            raise KeyError(title)
