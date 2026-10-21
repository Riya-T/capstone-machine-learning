"""Course enrollment: courses with a fixed number of seats, students, and
who is enrolled where.

Planted bug (initial version): add_course accepts a capacity of 0, since
it only refuses negative capacities. The public checks only try a
negative one.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from enrollment import Registrar
    registrar = Registrar()
    registrar.add_course("CS101", 30)
    registrar.add_student("ana")
    registrar.enroll("ana", "CS101")
"""


class EnrollmentError(Exception):
    pass


class CourseFull(EnrollmentError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_capacity(capacity):
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        raise ValueError(f"capacity must be an int greater than 0, got {capacity!r}")


class Registrar:
    def __init__(self):
        self._capacity = {}  # course id -> number of seats
        self._rosters = {}  # course id -> student ids, in enrollment order
        self._schedules = {}  # student id -> course ids, in enrollment order

    def add_course(self, course_id, capacity):
        check_id(course_id, "course_id")
        check_capacity(capacity)
        if course_id in self._capacity:
            raise EnrollmentError(f"course {course_id!r} already exists")
        self._capacity[course_id] = capacity
        self._rosters[course_id] = []

    def add_student(self, student_id):
        check_id(student_id, "student_id")
        if student_id in self._schedules:
            raise EnrollmentError(f"student {student_id!r} already exists")
        self._schedules[student_id] = []

    def enroll(self, student_id, course_id):
        self._require_student(student_id)
        self._require_course(course_id)
        if student_id in self._rosters[course_id]:
            raise EnrollmentError(f"{student_id!r} is already enrolled in {course_id!r}")
        if self._open_seats(course_id) == 0:
            raise CourseFull(f"course {course_id!r} has no open seat")
        self._rosters[course_id].append(student_id)
        self._schedules[student_id].append(course_id)

    def get_roster(self, course_id):
        self._require_course(course_id)
        return list(self._rosters[course_id])

    def get_schedule(self, student_id):
        self._require_student(student_id)
        return list(self._schedules[student_id])

    def get_open_seats(self, course_id):
        self._require_course(course_id)
        return self._open_seats(course_id)

    def _open_seats(self, course_id):
        return self._capacity[course_id] - len(self._rosters[course_id])

    # Non-str ids are never stored, so they count as "not added" too.
    def _require_student(self, student_id):
        if not isinstance(student_id, str) or student_id not in self._schedules:
            raise KeyError(student_id)

    def _require_course(self, course_id):
        if not isinstance(course_id, str) or course_id not in self._capacity:
            raise KeyError(course_id)
