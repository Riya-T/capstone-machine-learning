"""School roster with moves between grades and a cap per grade.

Correct solution for school_roster after c_move.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from roster import Roster
    roster = Roster(cap=25)
    roster.add_student("ana", 3)
    roster.move_students(["ana"], 4)
"""


class RosterError(Exception):
    pass


class GradeFull(RosterError):
    pass


def check_grade(grade):
    if isinstance(grade, bool) or not isinstance(grade, int) or not 1 <= grade <= 12:
        raise ValueError(f"grade must be an int from 1 to 12, got {grade!r}")


def check_cap(cap):
    if cap is not None and (isinstance(cap, bool) or not isinstance(cap, int) or cap < 1):
        raise ValueError(f"cap must be None or an int >= 1, got {cap!r}")


class Roster:
    def __init__(self, cap=None):
        check_cap(cap)
        self._cap = cap
        # name -> grade, in the order students joined their grade
        self._grade_of = {}

    def add_student(self, name, grade):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        check_grade(grade)
        if name in self._grade_of:
            raise RosterError(f"{name!r} is already on the roster")
        self._require_room(grade, 1)
        self._grade_of[name] = grade

    def get_grade(self, name):
        self._require(name)
        return self._grade_of[name]

    def get_students(self, grade):
        check_grade(grade)
        return [name for name, g in self._grade_of.items() if g == grade]

    def get_all_students(self):
        # A stable sort keeps arrival order within each grade.
        return sorted(self._grade_of, key=self._grade_of.__getitem__)

    def get_grades(self):
        return sorted(set(self._grade_of.values()))

    def get_cap(self):
        return self._cap

    def move_students(self, names, grade):
        check_grade(grade)
        for name in names:
            self._require(name)
        if len(set(names)) != len(names):
            raise ValueError("a name is listed more than once")
        arriving = [name for name in names if self._grade_of[name] != grade]
        self._require_room(grade, len(arriving))
        for name in arriving:
            # Re-inserting puts the student at the end of the new grade's order.
            del self._grade_of[name]
            self._grade_of[name] = grade

    def _require(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._grade_of:
            raise KeyError(name)

    def _require_room(self, grade, arriving):
        if self._cap is not None and len(self.get_students(grade)) + arriving > self._cap:
            raise GradeFull(f"grade {grade} cannot take {arriving} more students")
