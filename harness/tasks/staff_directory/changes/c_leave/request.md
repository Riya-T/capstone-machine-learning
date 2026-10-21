Let employees in `directory.py` go on leave.

- Add `Directory.start_leave(employee_id)`, `Directory.end_leave(employee_id)`
  and `Directory.is_on_leave(employee_id) -> bool`. All three raise
  `KeyError` for an id that is not employed. New hires are not on leave.
  Starting leave for an employee who is already on leave, or ending it for
  one who is not, does nothing.
- Add `class OnLeave(DirectoryError)` to `directory.py`.
- While an employee is on leave, `set_salary` for them raises `OnLeave` and
  changes nothing. `OnLeave` is checked after the `KeyError` and
  `ValueError` checks.
- `get_staff` takes a new keyword argument `include_on_leave=True`. With
  `include_on_leave=False` the employees on leave are left out and the rest
  keep their order. The argument must be a `bool`, or `ValueError` is
  raised; it is checked after the `KeyError` for a department that does not
  exist.
- Leave changes nothing else: `get_salary` and `get_department` work as
  before for an employee on leave, and the employee is still counted as a
  member of their department.

All existing behavior must keep working.
