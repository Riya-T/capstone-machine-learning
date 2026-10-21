Add free/busy queries to `agenda.py`, so a window of the day can be checked
for one person.

- Add `Agenda.get_busy(name, start, end) -> list[tuple[int, int]]`: the
  periods inside the window from `start` up to `end` during which the
  person attends at least one event. Each period is a `(from, to)` tuple
  cut down to the window, so no period starts before `start` or ends after
  `end`. Periods that overlap or touch are merged into one, so the result
  never has two periods where one ends exactly where the next begins. The
  periods come earliest first. Events entirely outside the window are
  ignored.
- Add `Agenda.get_free(name, start, end) -> list[tuple[int, int]]`: the
  gaps inside the window not covered by any busy period, earliest first. A
  person with nothing in the window gets `[(start, end)]`; a person busy for
  the whole window gets `[]`.
- Add `Agenda.is_free(name, start, end) -> bool`: `True` when the person
  attends no event that overlaps the window.
- The window follows the same rules as event times: `start` must be an
  `int` that is 0 or more and `end` an `int` greater than `start`, or
  `ValueError` is raised. A name that attends nothing is not an error; it
  is free for the whole window.
- These queries change nothing.

All existing behavior must keep working.
