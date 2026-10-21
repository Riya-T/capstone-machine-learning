"""Time clock with an adjustable overtime rule, shift corrections and a
version number per employee that guards against conflicting edits.

Correct solution for time_clock after c_overtime_rules and c_versions.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from timeclock import TimeClock
    clock = TimeClock()
    clock.add_employee("ana")
    clock.clock_in("ana", 540)
    clock.clock_out("ana", 1080, expected_version=2)
    clock.correct_shift("ana", 0, 540, 1020, expected_version=3)
"""

DEFAULT_OVERTIME_AFTER = 480  # minutes of a shift before overtime starts


class ClockError(Exception):
    pass


class VersionConflict(ClockError):
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
        self._shifts = {}  # employee id -> list of (start, end), sorted by start
        self._open = {}  # employee id -> clock-in minute, while clocked in
        self._thresholds = {}  # employee id -> overtime_after for that employee
        self._versions = {}  # employee id -> version number

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
        self._versions[employee_id] = 1

    def clock_in(self, employee_id, minute, expected_version=None):
        self._require(employee_id, expected_version)
        check_minute(minute)
        if employee_id in self._open:
            raise ClockError(f"employee {employee_id!r} is already clocked in")
        if minute < self._last_end(employee_id):
            raise ValueError(f"minute {minute} is before the end of an earlier shift")
        self._open[employee_id] = minute
        self._versions[employee_id] += 1

    def clock_out(self, employee_id, minute, expected_version=None):
        self._require(employee_id, expected_version)
        check_minute(minute)
        if employee_id not in self._open:
            raise ClockError(f"employee {employee_id!r} is not clocked in")
        start = self._open[employee_id]
        if minute <= start:
            raise ValueError(f"minute {minute} is not after the clock-in minute {start}")
        del self._open[employee_id]
        self._shifts[employee_id].append((start, minute))
        self._versions[employee_id] += 1

    def correct_shift(self, employee_id, index, start, end, expected_version=None):
        self._require(employee_id, expected_version)
        shifts = self._shifts[employee_id]
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(shifts):
            raise IndexError(index)
        check_minute(start)
        check_minute(end)
        if end <= start:
            raise ValueError(f"end {end} is not after start {start}")
        for i, (other_start, other_end) in enumerate(shifts):
            if i != index and other_start < end and start < other_end:
                raise ValueError(f"({start}, {end}) overlaps the shift {(other_start, other_end)}")
        open_start = self._open.get(employee_id)
        if open_start is not None and end > open_start:
            raise ValueError(f"end {end} is after the clock-in minute {open_start}")
        shifts[index] = (start, end)
        shifts.sort()
        self._versions[employee_id] += 1

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
        limit = self._thresholds[employee_id]
        return sum(max(0, end - start - limit) for start, end in self._shifts[employee_id])

    def get_overtime_after(self, employee_id):
        self._require(employee_id)
        return self._thresholds[employee_id]

    def set_overtime_after(self, employee_id, minutes, expected_version=None):
        self._require(employee_id, expected_version)
        check_overtime_after(minutes)
        self._thresholds[employee_id] = minutes
        self._versions[employee_id] += 1

    def get_version(self, employee_id):
        self._require(employee_id)
        return self._versions[employee_id]

    def _require(self, employee_id, expected_version=None):
        # Non-str ids are never stored, so they count as "not added" too.
        if not isinstance(employee_id, str) or employee_id not in self._shifts:
            raise KeyError(employee_id)
        current = self._versions[employee_id]
        if expected_version is not None and expected_version != current:
            raise VersionConflict(
                f"employee {employee_id!r} is at version {current}, not {expected_version!r}"
            )

    def _last_end(self, employee_id):
        return max((end for _, end in self._shifts[employee_id]), default=0)
