"""Job board with limits on applications per applicant and per job.

Correct solution for job_board after c_limit. Validation of an application
sits in one place, so the new limits slot in after the existing checks.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from board import JobBoard
    board = JobBoard(max_applications=5)
    board.post_job("j1", "Data Engineer", 90000, max_applicants=20)
"""


class BoardError(Exception):
    pass


class LimitReached(BoardError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_limit(value, what):
    if value is not None:
        check_positive(value, what)


class JobBoard:
    def __init__(self, max_applications=None):
        check_limit(max_applications, "max_applications")
        self._max_applications = max_applications
        self._jobs = {}  # job id -> (title, salary), in posting order
        self._max_applicants = {}  # job id -> limit or None
        self._applicants = {}  # name -> list of job ids applied to, in order
        self._applications = {}  # job id -> list of names, in order

    def post_job(self, job_id, title, salary, max_applicants=None):
        check_name(job_id, "job_id")
        if job_id in self._jobs:
            raise BoardError(f"job {job_id!r} is already posted")
        check_name(title, "title")
        check_positive(salary, "salary")
        check_limit(max_applicants, "max_applicants")
        self._jobs[job_id] = (title, salary)
        self._max_applicants[job_id] = max_applicants
        self._applications[job_id] = []

    def add_applicant(self, name):
        check_name(name, "name")
        if name in self._applicants:
            raise BoardError(f"applicant {name!r} is already registered")
        self._applicants[name] = []

    def apply(self, name, job_id):
        self._require_applicant(name)
        self._require_job(job_id)
        if job_id in self._applicants[name]:
            raise BoardError(f"{name!r} already applied to {job_id!r}")
        self._require_room(name, job_id)
        self._applicants[name].append(job_id)
        self._applications[job_id].append(name)

    def get_applicants(self, job_id):
        self._require_job(job_id)
        return list(self._applications[job_id])

    def get_applications(self, name):
        self._require_applicant(name)
        return list(self._applicants[name])

    def get_job(self, job_id):
        self._require_job(job_id)
        return self._jobs[job_id]

    def get_jobs(self):
        return list(self._jobs)

    def get_max_applicants(self, job_id):
        self._require_job(job_id)
        return self._max_applicants[job_id]

    def _require_room(self, name, job_id):
        limit = self._max_applications
        if limit is not None and len(self._applicants[name]) >= limit:
            raise LimitReached(f"{name!r} already has {limit} applications")
        limit = self._max_applicants[job_id]
        if limit is not None and len(self._applications[job_id]) >= limit:
            raise LimitReached(f"job {job_id!r} already has {limit} applicants")

    def _require_job(self, job_id):
        if not isinstance(job_id, str) or job_id not in self._jobs:
            raise KeyError(job_id)

    def _require_applicant(self, name):
        if not isinstance(name, str) or name not in self._applicants:
            raise KeyError(name)
