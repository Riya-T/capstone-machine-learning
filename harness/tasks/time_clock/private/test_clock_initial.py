"""Hidden tests for the initial time_clock spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest private/test_clock_initial.py
"""

import pytest
from timeclock import ClockError, TimeClock

BAD_MINUTES = [-1, 1.5, "10", None]
EMPLOYEES = ["ana", "ben"]


@pytest.fixture
def clock():
    c = TimeClock()
    for name in EMPLOYEES:
        c.add_employee(name)
    return c


def state(c, ids=EMPLOYEES):
    """Every employee's shifts and clock-in state, to check that a failed call
    changed nothing."""
    return {e: (c.get_shifts(e), c.get_open_shift(e)) for e in ids}


# --- employees ----------------------------------------------------------------


def test_a_new_employee_has_nothing_recorded(clock):
    assert clock.get_shifts("ana") == []
    assert clock.get_open_shift("ana") is None
    assert clock.get_worked_minutes("ana") == 0
    assert clock.get_overtime_minutes("ana") == 0


def test_an_empty_id_is_rejected():
    c = TimeClock()
    with pytest.raises(ValueError):
        c.add_employee("")
    with pytest.raises(KeyError):
        c.get_shifts("")


def test_adding_an_employee_twice_is_rejected(clock):
    clock.clock_in("ana", 10)
    clock.clock_out("ana", 70)
    clock.clock_in("ana", 100)
    before = state(clock)
    with pytest.raises(ClockError):
        clock.add_employee("ana")
    assert state(clock) == before


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.clock_in("carl", 10),
        lambda c: c.clock_out("carl", 10),
        lambda c: c.get_open_shift("carl"),
        lambda c: c.get_shifts("carl"),
        lambda c: c.get_worked_minutes("carl"),
        lambda c: c.get_overtime_minutes("carl"),
        lambda c: c.get_shifts(None),
        lambda c: c.clock_in(1, 10),
    ],
)
def test_employees_that_were_not_added_raise_key_error(clock, call):
    clock.clock_in("ana", 5)
    before = state(clock)
    with pytest.raises(KeyError):
        call(clock)
    assert state(clock) == before


# --- clocking in and out --------------------------------------------------------


def test_shifts_are_listed_oldest_first(clock):
    for start, end in [(0, 100), (100, 250), (400, 900)]:
        clock.clock_in("ana", start)
        clock.clock_out("ana", end)
    assert clock.get_shifts("ana") == [(0, 100), (100, 250), (400, 900)]
    assert clock.get_worked_minutes("ana") == 100 + 150 + 500


def test_employees_are_tracked_separately(clock):
    clock.clock_in("ana", 0)
    clock.clock_in("ben", 30)
    clock.clock_out("ana", 90)
    assert clock.get_shifts("ana") == [(0, 90)]
    assert clock.get_shifts("ben") == []
    assert clock.get_open_shift("ben") == 30


def test_a_shift_can_start_at_minute_zero(clock):
    clock.clock_in("ana", 0)
    assert clock.get_open_shift("ana") == 0
    clock.clock_out("ana", 1)
    assert clock.get_shifts("ana") == [(0, 1)]


def test_clocking_in_twice_is_rejected(clock):
    clock.clock_in("ana", 50)
    before = state(clock)
    with pytest.raises(ClockError):
        clock.clock_in("ana", 60)
    assert state(clock) == before


def test_clocking_out_twice_is_rejected(clock):
    clock.clock_in("ana", 50)
    clock.clock_out("ana", 80)
    before = state(clock)
    with pytest.raises(ClockError):
        clock.clock_out("ana", 90)
    assert state(clock) == before


def test_clock_out_before_clock_in_is_rejected(clock):
    clock.clock_in("ana", 300)
    before = state(clock)
    with pytest.raises(ValueError):
        clock.clock_out("ana", 299)
    assert state(clock) == before


def test_clock_in_may_not_go_back_before_a_finished_shift(clock):
    clock.clock_in("ana", 100)
    clock.clock_out("ana", 200)
    before = state(clock)
    with pytest.raises(ValueError):
        clock.clock_in("ana", 199)
    with pytest.raises(ValueError):
        clock.clock_in("ana", 50)
    assert state(clock) == before


def test_clock_in_may_start_right_when_the_last_shift_ended(clock):
    clock.clock_in("ana", 100)
    clock.clock_out("ana", 200)
    clock.clock_in("ana", 200)
    assert clock.get_open_shift("ana") == 200


def test_an_earlier_shift_of_another_employee_does_not_matter(clock):
    clock.clock_in("ben", 500)
    clock.clock_out("ben", 900)
    clock.clock_in("ana", 10)
    assert clock.get_open_shift("ana") == 10


@pytest.mark.parametrize("minute", BAD_MINUTES)
@pytest.mark.parametrize(
    "call",
    [lambda c, m: c.clock_in("ana", m), lambda c, m: c.clock_out("ben", m)],
    ids=["clock_in", "clock_out"],
)
def test_invalid_minutes_are_rejected(clock, call, minute):
    clock.clock_in("ben", 0)
    before = state(clock)
    with pytest.raises(ValueError):
        call(clock, minute)
    assert state(clock) == before


def test_an_unknown_employee_is_reported_before_a_bad_minute(clock):
    with pytest.raises(KeyError):
        clock.clock_in("carl", -1)
    with pytest.raises(KeyError):
        clock.clock_out("carl", None)


def test_a_bad_minute_is_reported_before_the_clock_in_state(clock):
    # ana is not clocked in, so clock_out also has a ClockError.
    with pytest.raises(ValueError):
        clock.clock_out("ana", -5)
    clock.clock_in("ben", 10)
    with pytest.raises(ValueError):
        clock.clock_in("ben", "20")


def test_the_clock_in_state_is_reported_before_an_early_minute(clock):
    clock.clock_in("ana", 100)
    # 50 is also earlier than the clock-in minute.
    with pytest.raises(ClockError):
        clock.clock_in("ana", 50)
    clock.clock_out("ana", 200)
    with pytest.raises(ClockError):
        clock.clock_out("ana", 150)


# --- overtime -------------------------------------------------------------------


def test_overtime_starts_after_480_minutes(clock):
    clock.clock_in("ana", 0)
    clock.clock_out("ana", 480)
    clock.clock_in("ben", 0)
    clock.clock_out("ben", 481)
    assert clock.get_overtime_minutes("ana") == 0
    assert clock.get_overtime_minutes("ben") == 1


def test_overtime_is_counted_per_shift(clock):
    # 300 + 300 minutes: 600 in all, but neither shift is longer than 480.
    clock.clock_in("ana", 0)
    clock.clock_out("ana", 300)
    clock.clock_in("ana", 1000)
    clock.clock_out("ana", 1300)
    assert clock.get_worked_minutes("ana") == 600
    assert clock.get_overtime_minutes("ana") == 0


def test_overtime_adds_up_over_shifts(clock):
    for start, end in [(0, 500), (1440, 1440 + 600), (3000, 3200)]:
        clock.clock_in("ana", start)
        clock.clock_out("ana", end)
    assert clock.get_overtime_minutes("ana") == 20 + 120
    assert clock.get_worked_minutes("ana") == 500 + 600 + 200


def test_a_long_shift_under_way_has_no_overtime_yet(clock):
    clock.clock_in("ana", 0)
    clock.clock_out("ana", 700)
    clock.clock_in("ana", 1000)
    assert clock.get_overtime_minutes("ana") == 220
    assert clock.get_worked_minutes("ana") == 700


def test_clocks_do_not_share_employees():
    first, second = TimeClock(), TimeClock()
    first.add_employee("ana")
    first.clock_in("ana", 5)
    with pytest.raises(KeyError):
        second.get_shifts("ana")
    second.add_employee("ana")
    assert second.get_open_shift("ana") is None
