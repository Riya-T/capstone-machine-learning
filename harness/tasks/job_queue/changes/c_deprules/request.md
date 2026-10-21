Let dependencies be added to jobs already in the queue in `jobs.py`, with
rules that keep the dependency graph sound.

- Add `JobQueue.add_dependency(job_id, dep_id)`, which makes `job_id` wait
  for `dep_id` as well. On success `dep_id` is appended to the end of
  `get_dependencies(job_id)`, and `get_ready_jobs` and `complete_job` take
  the new dependency into account from then on. A dependency on a job that
  is already completed is satisfied at once.
- The call is refused, and nothing changes, when:
  - `job_id` is not in the queue (`KeyError`), then when `dep_id` is not in
    the queue (`KeyError`);
  - `job_id` and `dep_id` are the same job (`ValueError`);
  - `job_id` is already completed (`QueueError`);
  - `dep_id` is already a dependency of `job_id` (`QueueError`);
  - the dependency would form a cycle, that is `dep_id` already depends on
    `job_id` either directly or through other jobs (`QueueError`).

  Several problems at once are reported in the order listed above.

All existing behavior must keep working.
