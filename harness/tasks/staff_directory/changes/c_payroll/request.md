Add payroll figures to `directory.py`.

- Add `Directory.get_payroll(department) -> int`: the sum of the salaries
  of the department's employees who are not on leave. Raises `KeyError` for
  a department that does not exist. An empty department, or one whose whole
  staff is on leave, has a payroll of 0.
- Add `Directory.get_total_payroll() -> int`: the sum of `get_payroll` over
  every department; 0 when there are no departments.
- Add `Directory.get_salary_history(employee_id) -> list[int]`: every
  salary the employee has had, oldest first, starting with the salary they
  were hired at and followed by one entry for each successful `set_salary`,
  even one that sets the same salary again. A `set_salary` that raises adds
  nothing. Raises `KeyError` for an id that is not employed.
- Payroll figures describe the directory as it stands when they are called:
  hiring, salary changes, starting leave and ending leave all change what
  later calls return.

All existing behavior must keep working.
