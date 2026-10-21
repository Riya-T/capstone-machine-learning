"""Hidden tests for the c_versions change (shift corrections and version
numbers). Never shown to the writer or the editor.

Usage (with timeclock.py importable, e.g. in the sandbox):
    python -m pytest changes/c_versions/private/test_versions_new.py
"""

import pytest
from timeclock import ClockError, TimeClock, VersionConflict

EMPLOYEES = ["ana", "ben"]


@pytest.fixture
def clock():
    """ana has shifts (0, 100) and (200, 300) and is at version 5; ben is new."""
    c = TimeClock()
    for name in EMPLOYEES:
        c.add_employee(name)
    for start, end in [(0, 100), (200, 300)]:
        c.clock_in("ana", start)
        c.clock_out("ana", end)
    return c


def state(c):
    return {
        e: (
            c.get_shifts(e),
            c.get_open_shift(e),
            c.get_overtime_after(e),
            c.get_version(e),
        )
        for e in EMPLOYEES
    }


CHANGES = {
    "clock_in": lambda c, v: c.clock_in("ana", 400, expected_version=v),
    "set_overtime_after": lambda c, v: c.set_overtime_after("ana", 60, expected_version=v),
    "correct_shift": lambda c, v: c.correct_shift("ana", 1, 150, 300, expected_version=v),
}


# --- versions -------------------------------------------------------------------


def test_version_counts_every_change(clock):
    assert clock.get_version("ana") == 5
    assert clock.get_version("ben") == 1
    clock.set_overtime_after("ben", 100)
    clock.clock_in("ben", 10)
    clock.clock_out("ben", 20)
    clock.correct_shift("ben", 0, 5, 25)
    assert clock.get_version("ben") == 5
    assert clock.get_version("ana") == 5


def test_version_does_not_change_on_reads(clock):
    for read in (
        clock.get_shifts,
        clock.get_open_shift,
        clock.get_worked_minutes,
        clock.get_overtime_minutes,
        clock.get_overtime_after,
        clock.get_version,
    ):
        read("ana")
    assert clock.get_version("ana") == 5


def test_version_does_not_change_on_failed_calls(clock):
    clock.clock_in("ana", 400)
    for call in (
        lambda: clock.clock_in("ana", 500),
        lambda: clock.clock_out("ana", 400),
        lambda: clock.clock_out("ana", -1),
        lambda: clock.set_overtime_after("ana", -1),
        lambda: clock.correct_shift("ana", 5, 0, 10),
        lambda: clock.correct_shift("ana", 0, 50, 250),
    ):
        with pytest.raises((ValueError, IndexError, ClockError)):
            call()
    assert clock.get_version("ana") == 6


@pytest.mark.parametrize("call", CHANGES.values(), ids=CHANGES.keys())
def test_version_that_matches_lets_the_change_through(clock, call):
    call(clock, 5)
    assert clock.get_version("ana") == 6


@pytest.mark.parametrize("stale", [1, 4, 6, "5"])
@pytest.mark.parametrize("call", CHANGES.values(), ids=CHANGES.keys())
def test_version_that_does_not_match_changes_nothing(clock, call, stale):
    before = state(clock)
    with pytest.raises(VersionConflict):
        call(clock, stale)
    assert state(clock) == before


def test_version_check_on_clock_out(clock):
    clock.clock_in("ana", 400)
    with pytest.raises(VersionConflict):
        clock.clock_out("ana", 450, expected_version=5)
    clock.clock_out("ana", 450, expected_version=6)
    assert clock.get_shifts("ana")[-1] == (400, 450)


def test_version_conflict_is_a_clock_error():
    assert issubclass(VersionConflict, ClockError)


def test_version_conflict_comes_right_after_an_unknown_employee(clock):
    with pytest.raises(KeyError):
        clock.clock_in("carl", 10, expected_version=99)
    with pytest.raises(KeyError):
        clock.get_version("carl")
    clock.clock_in("ana", 400)  # version 6
    before = state(clock)
    for call in (
        lambda: clock.clock_in("ana", -1, expected_version=1),
        lambda: clock.clock_in("ana", 500, expected_version=1),
        lambda: clock.clock_out("ben", 10, expected_version=7),
        lambda: clock.set_overtime_after("ana", None, expected_version=1),
        lambda: clock.correct_shift("ana", 9, 0, 1, expected_version=1),
        lambda: clock.correct_shift("ana", 0, 50, 10, expected_version=1),
    ):
        with pytest.raises(VersionConflict):
            call()
    assert state(clock) == before


# --- corrections ------------------------------------------------------------------


def test_correction_keeps_shifts_sorted_by_start(clock):
    clock.correct_shift("ana", 1, 120, 180)
    assert clock.get_shifts("ana") == [(0, 100), (120, 180)]
    clock.correct_shift("ana", 0, 500, 700)
    assert clock.get_shifts("ana") == [(120, 180), (500, 700)]
    assert clock.get_worked_minutes("ana") == 60 + 200


def test_correction_changes_overtime(clock):
    clock.set_overtime_after("ana", 90)
    assert clock.get_overtime_minutes("ana") == 20
    clock.correct_shift("ana", 0, 0, 50)
    assert clock.get_overtime_minutes("ana") == 10
    clock.correct_shift("ana", 1, 200, 400)
    assert clock.get_overtime_minutes("ana") == 110


def test_correction_may_touch_or_cover_its_own_old_times(clock):
    clock.correct_shift("ana", 0, 100, 200)
    assert clock.get_shifts("ana") == [(100, 200), (200, 300)]
    clock.correct_shift("ana", 1, 200, 350)
    assert clock.get_shifts("ana") == [(100, 200), (200, 350)]


@pytest.mark.parametrize("start, end", [(50, 250), (250, 260), (150, 201), (0, 1000)])
def test_correction_may_not_overlap_another_shift(clock, start, end):
    before = state(clock)
    with pytest.raises(ValueError):
        clock.correct_shift("ana", 0, start, end)
    assert state(clock) == before


def test_correction_may_not_run_past_the_shift_under_way(clock):
    clock.clock_in("ana", 400)
    before = state(clock)
    with pytest.raises(ValueError):
        clock.correct_shift("ana", 1, 200, 401)
    assert state(clock) == before
    clock.correct_shift("ana", 1, 200, 400)
    assert clock.get_shifts("ana") == [(0, 100), (200, 400)]


def test_correction_moves_the_earliest_allowed_clock_in(clock):
    clock.correct_shift("ana", 1, 150, 180)
    clock.clock_in("ana", 180)
    assert clock.get_open_shift("ana") == 180


@pytest.mark.parametrize("index", [-1, 2, 10, "0", None, 1.0])
def test_correction_needs_the_position_of_a_finished_shift(clock, index):
    before = state(clock)
    with pytest.raises(IndexError):
        clock.correct_shift("ana", index, 0, 50)
    assert state(clock) == before


def test_correction_of_an_employee_without_shifts_has_no_valid_position(clock):
    clock.clock_in("ben", 0)
    with pytest.raises(IndexError):
        clock.correct_shift("ben", 0, 0, 10)


@pytest.mark.parametrize(
    "start, end", [(-1, 50), (0, -1), (1.5, 50), (0, "50"), (None, 50), (60, 60), (60, 20)]
)
def test_correction_needs_valid_times(clock, start, end):
    before = state(clock)
    with pytest.raises(ValueError):
        clock.correct_shift("ana", 0, start, end)
    assert state(clock) == before


def test_correction_reports_a_bad_position_before_bad_times(clock):
    with pytest.raises(IndexError):
        clock.correct_shift("ana", 7, -1, -2)
    with pytest.raises(KeyError):
        clock.correct_shift("carl", 7, -1, -2)
