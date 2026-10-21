# Job queue

Write a module `jobs.py` that keeps a queue of jobs, each with a priority and
the jobs it has to wait for, and tracks which jobs have been completed.

## Interface

```python
class QueueError(Exception): ...


class JobQueue:
    def __init__(self): ...
    def add_job(self, job_id: str, priority: int, depends_on: list[str] | None = None) -> None: ...
    def complete_job(self, job_id: str) -> None: ...
    def get_ready_jobs(self) -> list[str]: ...
    def get_pending_jobs(self) -> list[str]: ...
    def get_completed_jobs(self) -> list[str]: ...
    def get_dependencies(self, job_id: str) -> list[str]: ...
    def get_priority(self, job_id: str) -> int: ...
```

## Adding jobs

- `add_job(job_id, priority, depends_on)` adds a job. `job_id` must be a
  non-empty `str` and `priority` an `int` (not a `bool`; negative values are
  fine), or `ValueError` is raised. An id that is already in the queue
  raises `QueueError`.
- `depends_on` lists the ids of the jobs this one has to wait for. Every one
  of them must already be in the queue, or `KeyError` is raised. Leaving it
  out means the job waits for nothing.
- `get_dependencies(job_id)` returns the ids the job waits for, in the order
  they were given. `get_priority(job_id)` returns its priority.
- Every method that takes a job id raises `KeyError` when the id is not in
  the queue, including values that are not strings at all, such as `None` or
  `1`.

## Completing jobs

- A job is **ready** when it is not completed and every job it depends on is
  completed. Jobs without dependencies are ready as soon as they are added.
- `complete_job(job_id)` marks the job completed. Completing a job that is
  already completed raises `QueueError`, and so does completing a job that
  is not ready because a dependency is still open.
- `get_ready_jobs()` returns the ready jobs, highest priority first. Jobs
  with equal priority keep the order they were added in.
- `get_pending_jobs()` returns every job that is not completed, ready or
  not, in the order they were added.
- `get_completed_jobs()` returns the completed jobs in the order they were
  completed.

When a call has several problems, the first of these is raised:

1. `ValueError` for an invalid id or priority passed to `add_job`;
2. `QueueError` for an id that is already in the queue;
3. `KeyError` for a job id that is not in the queue (a dependency in
   `add_job`, or the id passed to any other method);
4. `QueueError` for completing a job that is completed or not ready.

A failed call has no effect: if a method raises, the queue's jobs, their
dependencies and the completed list are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes listing the same dependency twice in `depends_on`, passing something
other than a list for `depends_on`, what happens if a returned list is
changed, the text of error messages, saving the queue to a file, and use from
several threads.
