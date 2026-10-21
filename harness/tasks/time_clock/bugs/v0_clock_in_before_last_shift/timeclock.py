"""Time clock: employees clock in and out, and their worked and overtime
minutes are counted from the finished shifts.

Planted bug (initial version): clock_in accepts a minute earlier than the
end of a finished shift. The public checks never try one, so only the
hidden initial tests catch it. Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from timeclock import TimeClock
    clock = TimeClock()
    clock.add_employee("ana")
    clock.clock_in("ana", 540)
    clock.clock_out("ana", 1080)
"""

OVERTIME_AFTER = 480  # minutes of a shift before overtime starts


class ClockError(Exception):
    pass


def check_minute(minute):
    if isinstance(minute, bool) or not isinstance(minute, int) or minute < 0:
        raise ValueError(f"minute must be an int >= 0, got {minute!r}")


class TimeClock:
    def __init__(self):
        self._shifts = {}  # employee id -> list of (start, end), oldest first
        self._open = {}  # employee id -> clock-in minute, while clocked in

    def add_employee(self, employee_id):
        if not isinstance(employee_id, str) or not employee_id:
            raise ValueError("employee_id must be a non-empty str")
        if employee_id in self._shifts:
            raise ClockError(f"employee {employee_id!r} was already added")
        self._shifts[employee_id] = []

    def clock_in(self, employee_id, minute):
        self._require(employee_id)
        check_minute(minute)
        if employee_id in self._open:
            raise ClockError(f"employee {employee_id!r} is already clocked in")
        self._open[employee_id] = minute

    def clock_out(self, employee_id, minute):
        self._require(employee_id)
        check_minute(minute)
        if employee_id not in self._open:
            raise ClockError(f"employee {employee_id!r} is not clocked in")
        start = self._open[employee_id]
        if minute <= start:
            raise ValueError(f"minute {minute} is not after the clock-in minute {start}")
        del self._open[employee_id]
        self._shifts[employee_id].append((start, minute))

    def get_open_shift(self, employee_id):
        self._require(employee_id)
        return self._open.get(employee_id)

    def get_shifts(self, employee_id):
        self._require(employee_id)
        return list(self._shifts[employee_id])

    def get_worked_minutes(self, employee_id):
        self._require(employee_id)
        return sum(end - start for start, end in self._shifts[employee_id])

    def get_overtime_minutes(self, employee_id):
        self._require(employee_id)
        return sum(
            max(0, end - start - OVERTIME_AFTER) for start, end in self._shifts[employee_id]
        )

    def _require(self, employee_id):
        # Non-str ids are never stored, so they count as "not added" too.
        if not isinstance(employee_id, str) or employee_id not in self._shifts:
            raise KeyError(employee_id)

    def _last_end(self, employee_id):
        return max((end for _, end in self._shifts[employee_id]), default=0)
