Add department headcount caps and transfers between departments to
`directory.py`.

- Add `Directory.set_cap(department, cap)`: the most employees the
  department may have. It raises `KeyError` for a department that does not
  exist, then `ValueError` unless `cap` is an `int` that is 0 or more (not a
  `bool`), then `DirectoryError` if the department already has more
  employees than `cap`. In each case nothing changes. Departments start
  with no cap at all, and setting a cap again replaces the earlier one.
- Add `class DepartmentFull(DirectoryError)` to `directory.py`.
- `hire` into a department that already has as many employees as its cap
  raises `DepartmentFull`. This is checked after every other `hire` error.
- Add `Directory.transfer(employee_ids, department)`, where `employee_ids`
  is a list of ids: moves every listed employee into the department, all of
  them or none. Afterwards they appear at the end of `get_staff(department)`
  in the order listed, and no longer in their old departments. Each keeps
  their salary. Errors, in this order:
  1. `KeyError` for a department that does not exist;
  2. `ValueError` if `employee_ids` is empty or lists the same id twice;
  3. `KeyError` for the first listed id that is not employed;
  4. `DirectoryError` if a listed employee is already in that department;
  5. `DepartmentFull` if the department would end up with more employees
     than its cap.
  Whenever `transfer` raises, nobody has moved.

All existing behavior must keep working.
