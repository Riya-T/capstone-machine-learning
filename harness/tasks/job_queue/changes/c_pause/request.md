Let jobs in `jobs.py` be paused, for example while an operator looks into a
problem.

- Add `class JobPaused(QueueError)` to `jobs.py`.
- Add `JobQueue.pause_job(job_id)`, `JobQueue.resume_job(job_id)` and
  `JobQueue.is_paused(job_id) -> bool`. All three raise `KeyError` for a job
  that is not in the queue. New jobs are not paused. Pausing a paused job, or
  resuming a job that is not paused, does nothing.
- `pause_job` raises `QueueError` for a job that is already completed.
  `resume_job` on a completed job does nothing.
- A paused job is left out of `get_ready_jobs` but stays in
  `get_pending_jobs`. Jobs that depend on it stay blocked until it is
  resumed and completed.
- `complete_job` on a paused job raises `JobPaused` and changes nothing.
  This is checked after the `KeyError` and already-completed `QueueError`
  checks and before the check that every dependency is completed.
- Pausing and resuming change neither the completed list nor any job's
  priority or dependencies.

All existing behavior must keep working.
