Let jobs that are no longer needed be cancelled in `jobs.py`.

- Add `JobQueue.cancel_job(job_id)`, which removes the job from the queue.
  It raises `KeyError` for a job that is not in the queue, then `QueueError`
  if the job is already completed, then `QueueError` if any job that is not
  completed depends on it. In each case nothing changes.
- A cancelled job is gone: it is no longer in `get_pending_jobs` or
  `get_ready_jobs`, and every method that takes a job id treats it as not in
  the queue (`KeyError`). The completed list is unchanged.
- The id of a cancelled job may be used again by `add_job`. The new job is a
  fresh job: it goes to the end of the add order and has only the
  dependencies given to `add_job`.
- Add `JobQueue.get_cancelled_jobs() -> list[str]`, the ids of cancelled
  jobs in the order they were cancelled. Every cancellation adds an entry, so
  an id that was added again and cancelled again appears twice.

All existing behavior must keep working.
