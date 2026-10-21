"""Course enrollment with prerequisites, dropping, and a first-come waiting
list that fills each seat given up.

Planted bug (after c_prerequisites and c_waitlist): the waiting list and
drop work, but enroll without waitlist=True now raises CourseFull before
it checks the prerequisites, so a full course hides a missing one.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from enrollment import Registrar
    registrar = Registrar()
    registrar.add_course("CS101", 1)
    registrar.add_student("ana")
    registrar.add_student("ben")
    registrar.enroll("ana", "CS101")
    registrar.enroll("ben", "CS101", waitlist=True)
    registrar.drop("ana", "CS101")  # ben now holds the seat
"""


class EnrollmentError(Exception):
    pass


class CourseFull(EnrollmentError):
    pass


class MissingPrerequisite(EnrollmentError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_capacity(capacity):
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError(f"capacity must be an int greater than 0, got {capacity!r}")


class Registrar:
    def __init__(self):
        self._capacity = {}  # course id -> number of seats
        self._prerequisites = {}  # course id -> course ids to complete first
        self._rosters = {}  # course id -> student ids, in enrollment order
        self._waitlists = {}  # course id -> waiting student ids, first in line first
        self._schedules = {}  # student id -> course ids, in enrollment order
        self._completed = {}  # student id -> completed course ids, in recorded order

    def add_course(self, course_id, capacity, prerequisites=()):
        check_id(course_id, "course_id")
        check_capacity(capacity)
        if course_id in self._capacity:
            raise EnrollmentError(f"course {course_id!r} already exists")
        for required in prerequisites:
            self._require_course(required)
        self._capacity[course_id] = capacity
        self._prerequisites[course_id] = list(prerequisites)
        self._rosters[course_id] = []
        self._waitlists[course_id] = []

    def add_student(self, student_id):
        check_id(student_id, "student_id")
        if student_id in self._schedules:
            raise EnrollmentError(f"student {student_id!r} already exists")
        self._schedules[student_id] = []
        self._completed[student_id] = []

    def enroll(self, student_id, course_id, waitlist=False):
        self._require_student(student_id)
        self._require_course(course_id)
        if student_id in self._rosters[course_id]:
            raise EnrollmentError(f"{student_id!r} is already enrolled in {course_id!r}")
        if student_id in self._waitlists[course_id]:
            raise EnrollmentError(f"{student_id!r} is already waiting for {course_id!r}")
        if not waitlist and self._open_seats(course_id) == 0:
            raise CourseFull(f"course {course_id!r} has no open seat")
        self._require_prerequisites(student_id, course_id)
        if self._open_seats(course_id) > 0:
            self._seat(student_id, course_id)
        else:
            self._waitlists[course_id].append(student_id)

    def drop(self, student_id, course_id):
        self._require_student(student_id)
        self._require_course(course_id)
        waiting = self._waitlists[course_id]
        if student_id in waiting:
            waiting.remove(student_id)
        elif student_id in self._rosters[course_id]:
            self._rosters[course_id].remove(student_id)
            self._schedules[student_id].remove(course_id)
            if waiting:
                self._seat(waiting.pop(0), course_id)
        else:
            raise EnrollmentError(f"{student_id!r} is not in or waiting for {course_id!r}")

    def record_completion(self, student_id, course_id):
        self._require_student(student_id)
        self._require_course(course_id)
        if course_id not in self._completed[student_id]:
            self._completed[student_id].append(course_id)

    def get_roster(self, course_id):
        self._require_course(course_id)
        return list(self._rosters[course_id])

    def get_waitlist(self, course_id):
        self._require_course(course_id)
        return list(self._waitlists[course_id])

    def get_schedule(self, student_id):
        self._require_student(student_id)
        return list(self._schedules[student_id])

    def get_open_seats(self, course_id):
        self._require_course(course_id)
        return self._open_seats(course_id)

    def get_completed(self, student_id):
        self._require_student(student_id)
        return list(self._completed[student_id])

    def _seat(self, student_id, course_id):
        self._rosters[course_id].append(student_id)
        self._schedules[student_id].append(course_id)

    def _open_seats(self, course_id):
        return self._capacity[course_id] - len(self._rosters[course_id])

    def _require_prerequisites(self, student_id, course_id):
        for required in self._prerequisites[course_id]:
            if required not in self._completed[student_id]:
                raise MissingPrerequisite(f"{student_id!r} has not completed {required!r}")

    # Non-str ids are never stored, so they count as "not added" too.
    def _require_student(self, student_id):
        if not isinstance(student_id, str) or student_id not in self._schedules:
            raise KeyError(student_id)

    def _require_course(self, course_id):
        if not isinstance(course_id, str) or course_id not in self._capacity:
            raise KeyError(course_id)
