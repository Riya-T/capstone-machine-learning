# Time clock

Write a module `timeclock.py` that records when employees clock in and out,
and counts the minutes they worked and the overtime they earned.

## Interface

```python
class ClockError(Exception): ...


class TimeClock:
    def __init__(self): ...
    def add_employee(self, employee_id: str) -> None: ...
    def clock_in(self, employee_id: str, minute: int) -> None: ...
    def clock_out(self, employee_id: str, minute: int) -> None: ...
    def get_open_shift(self, employee_id: str) -> int | None: ...
    def get_shifts(self, employee_id: str) -> list[tuple[int, int]]: ...
    def get_worked_minutes(self, employee_id: str) -> int: ...
    def get_overtime_minutes(self, employee_id: str) -> int: ...
```

Times are whole minutes, as `int`, counted from some starting point (minute
0). A minute must be an `int` that is 0 or more, or `ValueError` is raised.

## Employees

- `add_employee(employee_id)` adds an employee who is not clocked in and has
  no shifts. An empty id raises `ValueError`, and adding an id that was
  already added raises `ClockError`.
- Every other method raises `KeyError` when given an employee id that was
  not added, including values that are not strings at all, such as `None`
  or `1`.

## Clocking in and out

- `clock_in(employee_id, minute)` starts a shift at `minute`. Clocking in
  while already clocked in raises `ClockError`. The minute may not be
  earlier than the end of any of the employee's finished shifts (it may be
  equal to it); an earlier one raises `ValueError`.
- `clock_out(employee_id, minute)` ends the shift that is under way, which
  becomes a finished shift `(start, end)`. Clocking out while not clocked in
  raises `ClockError`. The minute must be later than the clock-in minute,
  or `ValueError` is raised.
- `get_open_shift(employee_id)` returns the clock-in minute of the shift
  under way, or `None` when the employee is not clocked in.

When a call has several problems, the first of these is raised:

1. `KeyError` for an employee that was not added;
2. `ValueError` for a minute that is not an `int` of 0 or more;
3. `ClockError` for clocking in while clocked in, or out while not;
4. `ValueError` for a minute that is too early.

## Totals

- `get_shifts(employee_id)` returns the employee's finished shifts as
  `(start, end)` tuples, oldest first. A shift under way is not included.
- `get_worked_minutes(employee_id)` returns the total length of the
  finished shifts (`end - start` each).
- `get_overtime_minutes(employee_id)` returns the overtime: in each finished
  shift, the minutes after its first 480 (eight hours) are overtime. A
  shift of 500 minutes has 20 overtime minutes, one of 480 or fewer has
  none. Overtime is counted per shift and then added up over all shifts.
- A shift under way counts towards none of these.

A failed call has no effect: if a method raises, every employee's shifts
and clock-in state are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_employee`, `bool` minutes,
what happens if a returned list is changed, the text of error messages,
saving the data to a file, and use from several threads.
