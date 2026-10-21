"""Hidden tests for the c_limits change (per-zone target limits). Never shown
to the writer or the editor.

Usage (with thermostat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limits/private/test_limits_new.py
"""

import pytest
from thermostat import Thermostat, ThermostatError

BAD_BOUNDS = [(1.5, 25), (15, "25"), (None, 25), (True, 25), (15, False), (26, 25)]


@pytest.fixture
def stat():
    s = Thermostat()
    s.add_zone("hall")
    s.add_zone("attic")
    s.set_limits("hall", 15, 25)
    return s


def state(s):
    return {z: (s.get_setting(z), s.get_limits(z)) for z in s.get_zones()}


def test_limits_are_returned_as_set(stat):
    assert stat.get_limits("hall") == (15, 25)
    assert stat.get_limits("attic") is None


def test_the_bounds_themselves_are_allowed(stat):
    stat.set_target("hall", 15)
    assert stat.get_setting("hall") == ("off", 15)
    stat.set_target("hall", 25)
    assert stat.get_setting("hall") == ("off", 25)


@pytest.mark.parametrize("temp", [14, 26, -40, 100])
def test_targets_outside_the_limits_change_nothing(stat, temp):
    before = state(stat)
    with pytest.raises(ValueError):
        stat.set_target("hall", temp)
    assert state(stat) == before


def test_limits_apply_per_zone(stat):
    stat.set_target("attic", 40)
    assert stat.get_setting("attic") == ("off", 40)
    with pytest.raises(ValueError):
        stat.set_target("hall", 40)


def test_equal_bounds_pin_the_target(stat):
    stat.set_target("attic", 18)
    stat.set_limits("attic", 18, 18)
    stat.set_target("attic", 18)
    with pytest.raises(ValueError):
        stat.set_target("attic", 19)
    with pytest.raises(ValueError):
        stat.set_target("attic", 17)


def test_readings_ignore_the_limits(stat):
    stat.record_reading("hall", 40)
    assert stat.get_reading("hall") == 40
    stat.record_reading("hall", -10)
    assert stat.get_reading("hall") == -10


def test_limits_can_be_replaced(stat):
    stat.set_limits("hall", 10, 30)
    assert stat.get_limits("hall") == (10, 30)
    stat.set_target("hall", 30)
    stat.set_limits("hall", 30, 35)
    stat.set_target("hall", 35)
    with pytest.raises(ValueError):
        stat.set_target("hall", 29)


def test_limits_that_exclude_the_current_target_are_rejected(stat):
    stat.set_target("hall", 22)
    before = state(stat)
    with pytest.raises(ThermostatError):
        stat.set_limits("hall", 23, 30)
    with pytest.raises(ThermostatError):
        stat.set_limits("hall", 10, 21)
    assert state(stat) == before


def test_the_default_target_must_fit_new_limits(stat):
    before = state(stat)
    with pytest.raises(ThermostatError):
        stat.set_limits("attic", 21, 30)
    assert state(stat) == before
    stat.set_limits("attic", 20, 30)
    assert stat.get_limits("attic") == (20, 30)


@pytest.mark.parametrize("low, high", BAD_BOUNDS)
def test_invalid_bounds_are_rejected(stat, low, high):
    before = state(stat)
    with pytest.raises(ValueError):
        stat.set_limits("hall", low, high)
    with pytest.raises(ValueError):
        stat.set_limits("attic", low, high)
    assert state(stat) == before


def test_bad_bounds_are_reported_before_the_target_check(stat):
    stat.set_target("attic", 50)
    with pytest.raises(ValueError):
        stat.set_limits("attic", 30, 10)


@pytest.mark.parametrize("zone", ["garage", None, 1])
def test_limit_methods_need_an_added_zone(stat, zone):
    with pytest.raises(KeyError):
        stat.set_limits(zone, 10, 30)
    with pytest.raises(KeyError):
        stat.set_limits(zone, 30, 10)
    with pytest.raises(KeyError):
        stat.get_limits(zone)
