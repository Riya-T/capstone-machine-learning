Make the overtime rule in `timeclock.py` adjustable, because different
sites and different contracts start overtime at different points of a shift.

- `TimeClock` takes a new keyword argument `overtime_after=480`: the number
  of minutes of a shift after which further minutes are overtime. It must
  be an `int` that is 0 or more; anything else raises `ValueError`. With
  0, every minute of a shift is overtime.
- `add_employee` takes a new keyword argument `overtime_after=None`. `None`
  means the employee uses the clock's value; anything else must be an `int`
  that is 0 or more, or `ValueError` is raised and no employee is added.
  When `add_employee` gets an invalid value together with another problem
  (for example an id that was already added), which error is raised is
  unspecified.
- Add `TimeClock.get_overtime_after(employee_id) -> int`, which returns the
  value that applies to the employee.
- Add `TimeClock.set_overtime_after(employee_id, minutes)`, which replaces
  the employee's value. It raises `KeyError` for an employee that was not
  added and `ValueError` for an invalid value (same rule as above; `None`
  is invalid here). Which is raised when both are wrong is unspecified. In
  each case nothing changes.
- `get_overtime_minutes` uses the employee's current value for every
  finished shift, including shifts finished before the value was changed.
- `get_overtime_after` raises `KeyError` for an employee that was not added.

All existing behavior must keep working.
