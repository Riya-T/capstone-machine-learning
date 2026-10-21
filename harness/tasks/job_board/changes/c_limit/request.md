Put limits on applications in `board.py`.

- `JobBoard` takes a new keyword argument `max_applications=None`: the most
  applications one applicant may have at a time on this board. `None` means
  no limit. Otherwise it must be an `int` greater than 0 (not a `bool`), or
  `ValueError` is raised.
- `post_job` takes a new keyword argument `max_applicants=None`: the most
  applicants the job accepts. `None` means no limit. Otherwise it must be an
  `int` greater than 0 (not a `bool`); anything else raises `ValueError`,
  reported after every other `post_job` error, and no job is posted.
- Add `JobBoard.get_max_applicants(job_id) -> int | None`, which returns the
  job's limit. It raises `KeyError` for a job id that was not posted.
- Add `class LimitReached(BoardError)` to `board.py`.
- `apply` raises `LimitReached` and changes nothing when the applicant
  already has `max_applications` applications, or otherwise when the job
  already has `max_applicants` applicants. `LimitReached` is checked last,
  after every other check `apply` makes.

All existing behavior must keep working.
