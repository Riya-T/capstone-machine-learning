Add ways to search the jobs in `board.py`.

- Add `JobBoard.find_jobs(keyword=None, min_salary=None, max_salary=None)
  -> list[str]`: the ids of every posted job that passes all the filters
  given, highest salary first, with equal salaries in the order the jobs
  were posted. With `keyword`, only jobs whose title contains it count,
  ignoring case. With `min_salary`, only jobs paying at least that much
  count; with `max_salary`, only jobs paying at most that much. With no
  filters, every job is returned.
- `find_jobs` raises `ValueError` if `keyword` is given but is not a
  non-empty string, then `ValueError` if `min_salary` or `max_salary` is
  given but is not an `int` that is 0 or more (a `bool` does not count),
  then `ValueError` if `min_salary` is greater than `max_salary`.
- Add `JobBoard.get_jobs_by_popularity() -> list[str]`: every posted job,
  the one with the most applicants first, with equal counts in the order the
  jobs were posted.

All existing behavior must keep working.
