Add department headcount caps and transfers between departments to
`directory.py`.

- Add `Directory.set_cap(department, cap)`: the most employees the
  department may have. It raises `KeyError` for a department that does not
  exist, `ValueError` unless `cap` is an `int` that is 0 or more, and
  `DirectoryError` if the department already has more employees than `cap`.
  In each case nothing changes. Departments start with no cap at all, and
  setting a cap again replaces the earlier one.
- Add `class DepartmentFull(DirectoryError)` to `directory.py`.
- `hire` into a department that already has as many employees as its cap
  raises `DepartmentFull`.
- Add `Directory.transfer(employee_ids, department)`, where `employee_ids`
  is a list of ids: moves every listed employee into the department, all of
  them or none. Afterwards they appear at the end of `get_staff(department)`
  in the order listed, and no longer in their old departments. Each keeps
  their salary. Errors:
  - `KeyError` for a department that does not exist;
  - `ValueError` if `employee_ids` is empty or lists the same id twice;
  - `KeyError` if a listed id is not employed;
  - `DirectoryError` if a listed employee is already in that department;
  - `DepartmentFull` if the department would end up with more employees
    than its cap.
  Whenever `transfer` raises, nobody has moved.
- Which error is raised when a `hire` into a full department also has
  another problem (such as a bad salary), or when one `set_cap` or
  `transfer` call has several of the problems above (such as an unknown
  employee in a transfer to a full department), is unspecified.

All existing behavior must keep working.
