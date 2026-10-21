"""Job board: posted jobs, registered applicants, and who applied to what.

Planted bug (initial version): an applicant can apply to the same job
twice. The public checks never apply twice, so only the hidden initial
tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from board import JobBoard
    board = JobBoard()
    board.post_job("j1", "Data Engineer", 90000)
    board.add_applicant("ann")
    board.apply("ann", "j1")
"""


class BoardError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


class JobBoard:
    def __init__(self):
        self._jobs = {}  # job id -> (title, salary), in posting order
        self._applicants = {}  # name -> list of job ids applied to, in order
        self._applications = {}  # job id -> list of names, in order

    def post_job(self, job_id, title, salary):
        check_name(job_id, "job_id")
        if job_id in self._jobs:
            raise BoardError(f"job {job_id!r} is already posted")
        check_name(title, "title")
        check_positive(salary, "salary")
        self._jobs[job_id] = (title, salary)
        self._applications[job_id] = []

    def add_applicant(self, name):
        check_name(name, "name")
        if name in self._applicants:
            raise BoardError(f"applicant {name!r} is already registered")
        self._applicants[name] = []

    def apply(self, name, job_id):
        self._require_applicant(name)
        self._require_job(job_id)
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

    def _require_job(self, job_id):
        if not isinstance(job_id, str) or job_id not in self._jobs:
            raise KeyError(job_id)

    def _require_applicant(self, name):
        if not isinstance(name, str) or name not in self._applicants:
            raise KeyError(name)
