Put limits on applications in `board.py`.

- `JobBoard` takes a new keyword argument `max_applications=None`: the most
  applications one applicant may have at a time on this board. `None` means
  no limit. Otherwise it must be an `int` greater than 0, or `ValueError` is
  raised.
- `post_job` takes a new keyword argument `max_applicants=None`: the most
  applicants the job accepts. `None` means no limit. Otherwise it must be an
  `int` greater than 0; anything else raises `ValueError`, and no job is
  posted.
- Add `JobBoard.get_max_applicants(job_id) -> int | None`, which returns the
  job's limit. It raises `KeyError` for a job id that was not posted.
- Add `class LimitReached(BoardError)` to `board.py`.
- `apply` raises `LimitReached` and changes nothing when the applicant
  already has `max_applications` applications, or when the job already has
  `max_applicants` applicants.
- When one call has several problems and at least one of them comes from
  this change (an invalid `max_applicants`, or a limit that is reached),
  which error it raises is unspecified.

All existing behavior must keep working.
