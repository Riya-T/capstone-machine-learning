# Staff directory

Write a module `directory.py` that keeps the departments, employees and
salaries of one company.

## Interface

```python
class DirectoryError(Exception): ...


class Directory:
    def __init__(self): ...
    def add_department(self, name: str) -> None: ...
    def hire(self, employee_id: str, department: str, salary: int) -> None: ...
    def set_salary(self, employee_id: str, salary: int) -> None: ...
    def get_salary(self, employee_id: str) -> int: ...
    def get_department(self, employee_id: str) -> str: ...
    def get_staff(self, department: str) -> list[str]: ...
    def get_departments(self) -> list[str]: ...
```

All salaries are monthly amounts in whole cents, as `int`.

## Departments

- `add_department(name)` adds an empty department. An empty name raises
  `ValueError`, and a name that is already a department raises
  `DirectoryError`.
- `get_departments()` returns the department names in the order they were
  added.
- `get_staff(department)` returns the ids of the department's employees in
  the order they were hired, or an empty list.
- Every method that takes a department raises `KeyError` when the department
  does not exist, including values that are not strings at all, such as
  `None` or `1`.

## Employees

- `hire(employee_id, department, salary)` adds an employee to a department.
  An empty id raises `ValueError`; a department that does not exist raises
  `KeyError`; a salary that is not an `int` greater than 0 raises
  `ValueError`; an id that is already employed raises `DirectoryError`.
  The checks happen in that order.
- `set_salary(employee_id, salary)` replaces the employee's salary. It
  raises `KeyError` for an id that is not employed, then `ValueError` for an
  invalid salary.
- `get_salary(employee_id)` returns the current salary and
  `get_department(employee_id)` the name of the employee's department. Both
  raise `KeyError` for an id that is not employed, including values that
  are not strings.

A failed call has no effect: if a method raises, every department, every
employee and every salary is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes names or ids that are not strings passed to `add_department` and
`hire`, `bool` salaries, what happens if a returned list is changed, the
text of error messages, saving the directory to a file, and use from several
threads.
