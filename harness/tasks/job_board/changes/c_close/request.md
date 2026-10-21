Let jobs in `board.py` be closed once the position is filled.

- Add `JobBoard.close_job(job_id)`, `JobBoard.reopen_job(job_id)` and
  `JobBoard.is_open(job_id) -> bool`. All three raise `KeyError` for a job
  id that was not posted. New jobs are open. Closing a closed job, or
  reopening an open one, does nothing.
- Add `class JobClosed(BoardError)` to `board.py`.
- While a job is closed, `apply` to it raises `JobClosed` and changes
  nothing. `JobClosed` is checked after both `KeyError` checks and before
  the check for a repeated application.
- A closed job keeps its applicants, is still listed by `get_jobs` and can
  still be read with `get_job`.
- Add `JobBoard.get_open_jobs() -> list[str]`: the ids of the jobs that are
  open, in the order they were posted.

All existing behavior must keep working.
