"""School roster: which students are in which grade.

Planted bug (initial version): add_student never checks whether the name
is already on the roster, so adding it again silently changes the grade.
The public checks never add a name twice, so only the hidden initial tests
catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from roster import Roster
    roster = Roster()
    roster.add_student("ana", 3)
    roster.get_students(3)  # ["ana"]
"""


class RosterError(Exception):
    pass


def check_grade(grade):
    if isinstance(grade, bool) or not isinstance(grade, int) or not 1 <= grade <= 12:
        raise ValueError(f"grade must be an int from 1 to 12, got {grade!r}")


class Roster:
    def __init__(self):
        # name -> grade, in the order students joined their grade
        self._grade_of = {}

    def add_student(self, name, grade):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        check_grade(grade)
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

    def _require(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._grade_of:
            raise KeyError(name)
