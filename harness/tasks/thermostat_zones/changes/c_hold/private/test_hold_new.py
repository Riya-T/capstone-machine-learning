"""Hidden tests for the c_hold change (zones on hold). Never shown to the
writer or the editor.

Usage (with thermostat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_hold/private/test_hold_new.py
"""

import pytest
from thermostat import Thermostat, ThermostatError, ZoneHeld


@pytest.fixture
def stat():
    s = Thermostat()
    s.add_zone("hall")
    s.add_zone("attic")
    s.set_mode("hall", "heat")
    s.set_target("hall", 22)
    s.record_reading("hall", 18)
    return s


def state(s):
    result = {}
    for zone in s.get_zones():
        try:
            reading = s.get_reading(zone)
        except ThermostatError:
            reading = None
        result[zone] = (s.get_setting(zone), reading, s.is_held(zone))
    return result


def test_zones_start_released(stat):
    assert not stat.is_held("hall")
    assert not stat.is_held("attic")


def test_holding_or_releasing_twice_is_harmless(stat):
    stat.hold("hall")
    stat.hold("hall")
    assert stat.is_held("hall")
    stat.release("hall")
    stat.release("hall")
    assert not stat.is_held("hall")
    assert not stat.is_held("attic")


@pytest.mark.parametrize("method", ["hold", "release", "is_held"])
@pytest.mark.parametrize("zone", ["garage", None, 1])
def test_hold_methods_need_an_added_zone(stat, method, zone):
    with pytest.raises(KeyError):
        getattr(stat, method)(zone)


def test_set_target_on_a_held_zone_changes_nothing(stat):
    stat.hold("hall")
    before = state(stat)
    with pytest.raises(ZoneHeld):
        stat.set_target("hall", 30)
    assert state(stat) == before


def test_set_mode_on_a_held_zone_changes_nothing(stat):
    stat.hold("hall")
    before = state(stat)
    with pytest.raises(ZoneHeld):
        stat.set_mode("hall", "cool")
    assert state(stat) == before


def test_holding_one_zone_leaves_the_others_free(stat):
    stat.hold("hall")
    stat.set_target("attic", 15)
    stat.set_mode("attic", "cool")
    assert stat.get_setting("attic") == ("cool", 15)
    assert not stat.is_held("attic")


def test_readings_and_queries_work_while_held(stat):
    stat.hold("hall")
    stat.record_reading("hall", 21)
    assert stat.get_reading("hall") == 21
    assert stat.get_setting("hall") == ("heat", 22)
    assert stat.get_zones() == ["hall", "attic"]


def test_holding_keeps_mode_target_and_readings(stat):
    stat.hold("hall")
    stat.release("hall")
    assert stat.get_setting("hall") == ("heat", 22)
    assert stat.get_reading("hall") == 18


def test_bad_input_is_reported_before_the_hold(stat):
    stat.hold("hall")
    with pytest.raises(ValueError):
        stat.set_target("hall", 21.5)
    with pytest.raises(ValueError):
        stat.set_mode("hall", "warm")
    with pytest.raises(KeyError):
        stat.set_target("garage", 21)


def test_zone_held_is_a_thermostat_error():
    assert issubclass(ZoneHeld, ThermostatError)


def test_a_released_zone_accepts_changes_again(stat):
    stat.hold("hall")
    stat.release("hall")
    stat.set_mode("hall", "cool")
    stat.set_target("hall", 19)
    assert stat.get_setting("hall") == ("cool", 19)
