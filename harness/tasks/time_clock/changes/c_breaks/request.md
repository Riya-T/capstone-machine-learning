Record unpaid breaks in `timeclock.py`, and pay and count overtime only for
the time actually worked.

- Add `TimeClock.start_break(employee_id, minute, expected_version=None)`
  and `TimeClock.end_break(employee_id, minute, expected_version=None)`.
  A break belongs to the shift under way; a shift can have any number of
  breaks, one after another.
- `start_break` raises, in this order: `KeyError` for an employee that was
  not added; `VersionConflict` as for every other change; `ValueError` for
  a minute that is not an `int` of 0 or more; `ClockError` when the
  employee is not clocked in or is already on a break; `ValueError` when
  the minute is earlier than the clock-in minute or earlier than the end of
  an earlier break of the same shift (equal is allowed).
- `end_break` raises, in this order: `KeyError`; `VersionConflict`;
  `ValueError` for a minute that is not an `int` of 0 or more; `ClockError`
  when the employee is not on a break; `ValueError` when the minute is not
  later than the minute the break started.
- Both count as changes to the employee: on success the version goes up by 1.
- `clock_out` raises `ClockError` while the employee is on a break (where
  it already raises `ClockError` for an employee who is not clocked in),
  and `ValueError` when the minute is earlier than the end of one of the
  shift's breaks (where it already checks the clock-in minute; a break may
  end exactly at the clock-out minute).
- Add `TimeClock.get_break_minutes(employee_id) -> int`: the total length
  of the breaks of all finished shifts.
- Add `TimeClock.get_paid_minutes(employee_id) -> int`: the worked minutes
  minus the break minutes, over all finished shifts.
- Overtime is now counted on the paid minutes of each shift: a shift's
  overtime is its length minus its breaks, minus the employee's overtime
  value, and never below 0. A shift without breaks has the same overtime
  as before.
- `get_shifts` and `get_worked_minutes` still give the full shift times,
  breaks included. A shift under way and its breaks count towards none of
  the totals.
- `correct_shift` keeps the shift's breaks. The corrected shift must still
  contain every one of them (start no later than the first break starts,
  end no earlier than the last break ends); otherwise it raises
  `ValueError` after its other checks and changes nothing.
- `get_break_minutes` and `get_paid_minutes` raise `KeyError` for an
  employee that was not added.

All existing behavior must keep working.
