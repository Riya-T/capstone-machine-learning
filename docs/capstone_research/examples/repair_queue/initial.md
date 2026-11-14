# Repair Queue

Implement RepairQueue in repairs.py. RepairQueue() starts empty.
Job IDs and owners are nonempty strings and are compared as written.
Raise ValueError for a malformed string, duplicate job ID or invalid
transition. Raise KeyError when a syntactically valid job ID is required
to exist but is absent. A failed operation changes nothing. Exact error
text is unimportant.

- add(job_id, owner) -> None creates a waiting job. A job ID is unique
  across the queue and remains reserved while the job exists.
- start(job_id) -> None changes a waiting job to active.
- finish(job_id) -> None changes an active job to done.
- get(job_id) -> tuple returns (job_id, owner, state).
- jobs(state=None) -> list[tuple] returns a fresh list of these tuples in
  original creation order. Filter by state if supplied. Allowed states
  are "waiting", "active", and "done". An invalid filter raises ValueError.

For example, add "z" for "lee", add "a" for "kim", then start "a".
jobs() returns [("z", "lee", "waiting"), ("a", "kim", "active")].
Finishing "z" raises ValueError.
