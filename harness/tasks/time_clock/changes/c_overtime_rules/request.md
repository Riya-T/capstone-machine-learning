Make the overtime rule in `timeclock.py` adjustable, because different
sites and different contracts start overtime at different points of a shift.

- `TimeClock` takes a new keyword argument `overtime_after=480`: the number
  of minutes of a shift after which further minutes are overtime. It must
  be an `int` that is 0 or more (not a `bool`); anything else raises
  `ValueError`. With 0, every minute of a shift is overtime.
- `add_employee` takes a new keyword argument `overtime_after=None`. `None`
  means the employee uses the clock's value; anything else must be an `int`
  that is 0 or more (not a `bool`), or `ValueError` is raised and no
  employee is added. The `ValueError` checks of `add_employee` come before
  the `ClockError` for an id that was already added; if both the id and the
  value are invalid, either `ValueError` may come first.
- Add `TimeClock.get_overtime_after(employee_id) -> int`, which returns the
  value that applies to the employee.
- Add `TimeClock.set_overtime_after(employee_id, minutes)`, which replaces
  the employee's value. It raises `KeyError` for an employee that was not
  added, then `ValueError` for an invalid value (same rule as above; `None`
  is invalid here). In each case nothing changes.
- `get_overtime_minutes` uses the employee's current value for every
  finished shift, including shifts finished before the value was changed.
- `get_overtime_after` raises `KeyError` for an employee that was not added.

All existing behavior must keep working.
