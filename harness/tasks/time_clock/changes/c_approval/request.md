Let a manager approve finished shifts in `timeclock.py`, and let mistaken
shifts be removed as long as they have not been approved.

- Add `class ShiftApproved(ClockError)` to `timeclock.py`.
- Every finished shift is either approved or not. A shift is not approved
  when it is finished.
- Add `TimeClock.approve_shifts(employee_id) -> int`. It approves every
  finished shift of the employee that is not approved yet and returns how
  many it approved (0 when there were none). A shift under way is not
  affected; it starts out not approved once it is finished.
- Add `TimeClock.get_unapproved_shifts(employee_id) -> list[tuple[int, int]]`:
  the employee's finished shifts that are not approved, as `(start, end)`
  tuples in the same order as `get_shifts`.
- Add `TimeClock.remove_shift(employee_id, index)`, which removes the
  finished shift at position `index` of `get_shifts(employee_id)` (0 is the
  oldest). It raises, in this order: `KeyError` for an employee that was
  not added; `IndexError` when `index` is not an `int` from 0 up to the
  number of finished shifts minus 1 (negative positions are invalid);
  `ShiftApproved` when that shift is approved. In each case nothing changes.
- An approved shift is final: no method may change or remove it. Approving
  changes nothing else; worked and overtime minutes still include approved
  and unapproved shifts alike, and a removed shift no longer counts.
- After a removal, clocking in only has to respect the shifts that are
  left.
- `approve_shifts` and `get_unapproved_shifts` raise `KeyError` for an
  employee that was not added.

All existing behavior must keep working.
