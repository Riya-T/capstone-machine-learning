"""Job board with closable jobs and job search.

Correct solution for job_board after c_close and c_search.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from board import JobBoard
    board = JobBoard()
    board.post_job("j1", "Data Engineer", 90000)
    board.find_jobs(keyword="data", min_salary=80000)
"""


class BoardError(Exception):
    pass


class JobClosed(BoardError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_non_negative(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{what} must be an int >= 0, got {value!r}")


class JobBoard:
    def __init__(self):
        self._jobs = {}  # job id -> (title, salary), in posting order
        self._closed = set()  # job ids that are closed
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
        if job_id in self._closed:
            raise JobClosed(f"job {job_id!r} is closed")
        if job_id in self._applicants[name]:
            raise BoardError(f"{name!r} already applied to {job_id!r}")
        self._applicants[name].append(job_id)
        self._applications[job_id].append(name)

    def close_job(self, job_id):
        self._require_job(job_id)
        self._closed.add(job_id)

    def reopen_job(self, job_id):
        self._require_job(job_id)
        self._closed.discard(job_id)

    def is_open(self, job_id):
        self._require_job(job_id)
        return job_id not in self._closed

    def get_open_jobs(self):
        return [job_id for job_id in self._jobs if job_id not in self._closed]

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

    def find_jobs(self, keyword=None, min_salary=None, max_salary=None):
        if keyword is not None:
            check_name(keyword, "keyword")
            keyword = keyword.lower()
        if min_salary is not None:
            check_non_negative(min_salary, "min_salary")
        if max_salary is not None:
            check_non_negative(max_salary, "max_salary")
        if min_salary is not None and max_salary is not None and min_salary > max_salary:
            raise ValueError("min_salary must not be greater than max_salary")
        found = [
            job_id
            for job_id, (title, salary) in self._jobs.items()
            if (keyword is None or keyword in title.lower())
            and (min_salary is None or salary >= min_salary)
            and (max_salary is None or salary <= max_salary)
        ]
        # sorted is stable, so equal salaries keep posting order.
        return sorted(found, key=lambda job_id: -self._jobs[job_id][1])

    def get_jobs_by_popularity(self):
        return sorted(self._jobs, key=lambda job_id: -len(self._applications[job_id]))

    def _require_job(self, job_id):
        if not isinstance(job_id, str) or job_id not in self._jobs:
            raise KeyError(job_id)

    def _require_applicant(self, name):
        if not isinstance(name, str) or name not in self._applicants:
            raise KeyError(name)
