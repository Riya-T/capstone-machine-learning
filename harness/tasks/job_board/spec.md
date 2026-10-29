# Job board

Write a module `board.py` that keeps the jobs posted on a job board, the
people who registered as applicants, and who applied to which job.

## Interface

```python
class BoardError(Exception): ...


class JobBoard:
    def __init__(self): ...
    def post_job(self, job_id: str, title: str, salary: int) -> None: ...
    def add_applicant(self, name: str) -> None: ...
    def apply(self, name: str, job_id: str) -> None: ...
    def get_applicants(self, job_id: str) -> list[str]: ...
    def get_applications(self, name: str) -> list[str]: ...
    def get_job(self, job_id: str) -> tuple[str, int]: ...
    def get_jobs(self) -> list[str]: ...
```

Salaries are whole dollars per year, as `int`.

## Jobs

- `post_job(job_id, title, salary)` posts a job. An empty job id raises
  `ValueError`, and a job id that is already posted raises `BoardError`.
  The title must be a non-empty string and the salary an `int` greater
  than 0, or `ValueError` is raised.
- `get_job(job_id)` returns the job's `(title, salary)`.
- `get_jobs()` returns the ids of all posted jobs, in the order they were
  posted.
- `apply`, `get_applicants` and `get_job` raise `KeyError` for a job id that
  was not posted, including values that are not strings at all, such as
  `None`.

When `post_job` has several problems, the first of these is raised:

1. `ValueError` for an empty job id;
2. `BoardError` for a job id that is already posted;
3. `ValueError` for an invalid title;
4. `ValueError` for an invalid salary.

## Applicants

- `add_applicant(name)` registers an applicant. An empty name raises
  `ValueError`, and a name that is already registered raises `BoardError`.
- `apply` and `get_applications` raise `KeyError` for a name that is not
  registered, including values that are not strings at all.

## Applications

- `apply(name, job_id)` records that the applicant applied to the job. An
  applicant can apply to a job only once: applying again raises
  `BoardError`.
- `get_applicants(job_id)` returns the names of everyone who applied to the
  job, in the order they applied.
- `get_applications(name)` returns the ids of the jobs the applicant applied
  to, in the order they applied.

When `apply` has several problems, the first of these is raised:

1. `KeyError` for a name that is not registered;
2. `KeyError` for a job id that was not posted;
3. `BoardError` for an application that was already made.

A failed call has no effect: if a method raises, every job, applicant and
application is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes job ids and names that are not strings passed to `post_job` and
`add_applicant`, titles that are neither strings nor `None`, `bool`
salaries, what happens if a returned list is
changed, the text of error messages, saving the board to a file, and use
from several threads.
