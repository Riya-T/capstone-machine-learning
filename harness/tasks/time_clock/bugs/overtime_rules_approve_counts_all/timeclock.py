"""Time clock with shift approval, removal of unapproved shifts and an
adjustable overtime rule, per clock and per employee.

Planted bug (after c_approval and c_overtime_rules): the overtime rule
is adjustable, but approve_shifts returns the number of all finished
shifts instead of the newly approved ones. Never shown to the writer or
the editor; validate-tasks checks that the tests catch it.

Usage:
    from timeclock import TimeClock
    clock = TimeClock(overtime_after=420)
    clock.add_employee("ana")
    clock.clock_in("ana", 540)
    clock.clock_out("ana", 1080)
    clock.approve_shifts("ana")  # 1
"""

DEFAULT_OVERTIME_AFTER = 480  # minutes of a shift before overtime starts


class ClockError(Exception):
    pass


class ShiftApproved(ClockError):
    pass


def check_minute(minute):
    if isinstance(minute, bool) or not isinstance(minute, int) or minute < 0:
        raise ValueError(f"minute must be an int >= 0, got {minute!r}")


def check_overtime_after(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"overtime_after must be an int >= 0, got {value!r}")


class TimeClock:
    def __init__(self, overtime_after=DEFAULT_OVERTIME_AFTER):
        check_overtime_after(overtime_after)
        self._overtime_after = overtime_after
        # employee id -> list of [start, end, approved], oldest first
        self._shifts = {}
        self._open = {}  # employee id -> clock-in minute, while clocked in
        self._thresholds = {}  # employee id -> overtime_after for that employee

    def add_employee(self, employee_id, overtime_after=None):
        if not isinstance(employee_id, str) or not employee_id:
            raise ValueError("employee_id must be a non-empty str")
        if overtime_after is None:
            overtime_after = self._overtime_after
        check_overtime_after(overtime_after)
        if employee_id in self._shifts:
            raise ClockError(f"employee {employee_id!r} was already added")
        self._shifts[employee_id] = []
        self._thresholds[employee_id] = overtime_after

    def clock_in(self, employee_id, minute):
        self._require(employee_id)
        check_minute(minute)
        if employee_id in self._open:
            raise ClockError(f"employee {employee_id!r} is already clocked in")
        if minute < self._last_end(employee_id):
            raise ValueError(f"minute {minute} is before the end of an earlier shift")
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
        self._shifts[employee_id].append([start, minute, False])

    def approve_shifts(self, employee_id):
        self._require(employee_id)
        count = 0
        for shift in self._shifts[employee_id]:
            shift[2] = True
            count += 1
        return count

    def get_unapproved_shifts(self, employee_id):
        self._require(employee_id)
        return [(start, end) for start, end, approved in self._shifts[employee_id] if not approved]

    def remove_shift(self, employee_id, index):
        self._require(employee_id)
        shifts = self._shifts[employee_id]
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(shifts):
            raise IndexError(index)
        if shifts[index][2]:
            raise ShiftApproved(f"shift {index} of {employee_id!r} is approved")
        del shifts[index]

    def get_open_shift(self, employee_id):
        self._require(employee_id)
        return self._open.get(employee_id)

    def get_shifts(self, employee_id):
        self._require(employee_id)
        return [(start, end) for start, end, _ in self._shifts[employee_id]]

    def get_worked_minutes(self, employee_id):
        self._require(employee_id)
        return sum(end - start for start, end, _ in self._shifts[employee_id])

    def get_overtime_minutes(self, employee_id):
        self._require(employee_id)
        limit = self._thresholds[employee_id]
        return sum(max(0, end - start - limit) for start, end, _ in self._shifts[employee_id])

    def get_overtime_after(self, employee_id):
        self._require(employee_id)
        return self._thresholds[employee_id]

    def set_overtime_after(self, employee_id, minutes):
        self._require(employee_id)
        check_overtime_after(minutes)
        self._thresholds[employee_id] = minutes

    def _require(self, employee_id):
        # Non-str ids are never stored, so they count as "not added" too.
        if not isinstance(employee_id, str) or employee_id not in self._shifts:
            raise KeyError(employee_id)

    def _last_end(self, employee_id):
        return max((end for _, end, _ in self._shifts[employee_id]), default=0)
