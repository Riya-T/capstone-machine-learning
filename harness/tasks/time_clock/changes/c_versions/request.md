Let managers correct finished shifts in `timeclock.py`, and stop two people
from overwriting each other's edits to the same employee.

Versions:

- Add `class VersionConflict(ClockError)` to `timeclock.py`.
- Every employee has a version number. It is 1 right after `add_employee`
  and goes up by 1 with every successful call that changes that employee:
  `clock_in`, `clock_out`, `set_overtime_after`, `correct_shift` (below),
  and any other method that changes an employee. Calls that raise, and
  calls that only read, leave it unchanged. Other employees' versions are
  not affected.
- Add `TimeClock.get_version(employee_id) -> int`. It raises `KeyError`
  for an employee that was not added.
- Every method that changes an employee takes a new keyword argument
  `expected_version=None`. When it is not `None` and is not equal to the
  employee's current version, the call raises `VersionConflict` and changes
  nothing. `VersionConflict` is checked right after the `KeyError` for an
  employee that was not added, before every other error.

Corrections:

- Add `TimeClock.correct_shift(employee_id, index, start, end,
  expected_version=None)`, which replaces the finished shift at position
  `index` of `get_shifts(employee_id)` (0 is the oldest) with `(start, end)`.
- After the `KeyError` and `VersionConflict` checks, it raises, in this
  order:
  1. `IndexError` when `index` is not an `int` from 0 up to the number of
     finished shifts minus 1 (negative positions are invalid);
  2. `ValueError` when `start` or `end` is not an `int` of 0 or more, or
     `end` is not later than `start`;
  3. `ValueError` when the corrected shift would overlap another finished
     shift of the employee (shifts that only touch, one ending at the
     minute the other starts, do not overlap), or when the employee is
     clocked in and `end` is later than the clock-in minute.
- `get_shifts` stays sorted by start, oldest first, after a correction, and
  worked and overtime minutes follow the corrected times.

All existing behavior must keep working.
