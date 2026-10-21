"""Course enrollment where enrolling in a course can be frozen and a course
can require other courses to be completed first.

Planted bug (after c_freeze and c_prerequisites): prerequisites work, but
the freeze check moved below the already-enrolled and prerequisite
checks, so an enrolled student retrying a frozen course gets
EnrollmentError instead of CourseFrozen.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from enrollment import Registrar
    registrar = Registrar()
    registrar.add_course("CS101", 30)
    registrar.add_course("CS201", 20, prerequisites=["CS101"])
    registrar.freeze_course("CS201")
"""


class EnrollmentError(Exception):
    pass


class CourseFull(EnrollmentError):
    pass


class CourseFrozen(EnrollmentError):
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
        self._schedules = {}  # student id -> course ids, in enrollment order
        self._completed = {}  # student id -> completed course ids, in recorded order
        self._frozen = set()  # ids of frozen courses

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

    def add_student(self, student_id):
        check_id(student_id, "student_id")
        if student_id in self._schedules:
            raise EnrollmentError(f"student {student_id!r} already exists")
        self._schedules[student_id] = []
        self._completed[student_id] = []

    def enroll(self, student_id, course_id):
        self._require_student(student_id)
        self._require_course(course_id)
        if student_id in self._rosters[course_id]:
            raise EnrollmentError(f"{student_id!r} is already enrolled in {course_id!r}")
        self._require_prerequisites(student_id, course_id)
        if course_id in self._frozen:
            raise CourseFrozen(f"course {course_id!r} is frozen")
        if self._open_seats(course_id) == 0:
            raise CourseFull(f"course {course_id!r} has no open seat")
        self._rosters[course_id].append(student_id)
        self._schedules[student_id].append(course_id)

    def record_completion(self, student_id, course_id):
        self._require_student(student_id)
        self._require_course(course_id)
        if course_id not in self._completed[student_id]:
            self._completed[student_id].append(course_id)

    def freeze_course(self, course_id):
        self._require_course(course_id)
        self._frozen.add(course_id)

    def unfreeze_course(self, course_id):
        self._require_course(course_id)
        self._frozen.discard(course_id)

    def is_frozen(self, course_id):
        self._require_course(course_id)
        return course_id in self._frozen

    def get_roster(self, course_id):
        self._require_course(course_id)
        return list(self._rosters[course_id])

    def get_schedule(self, student_id):
        self._require_student(student_id)
        return list(self._schedules[student_id])

    def get_open_seats(self, course_id):
        self._require_course(course_id)
        return self._open_seats(course_id)

    def get_completed(self, student_id):
        self._require_student(student_id)
        return list(self._completed[student_id])

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
