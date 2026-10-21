"""Public checks for thermostat.py.

Usage (with thermostat.py importable, e.g. in the sandbox):
    python -m pytest public/test_thermostat_public.py
"""

import pytest
from thermostat import Thermostat, ThermostatError


@pytest.fixture
def stat():
    s = Thermostat()
    s.add_zone("attic")
    s.add_zone("hall")
    return s


def test_a_new_zone_is_off_at_twenty_degrees(stat):
    assert stat.get_setting("hall") == ("off", 20)
    assert stat.get_zones() == ["attic", "hall"]


def test_target_and_mode_can_be_changed(stat):
    stat.set_target("hall", 23)
    stat.set_mode("hall", "heat")
    assert stat.get_setting("hall") == ("heat", 23)
    assert stat.get_setting("attic") == ("off", 20)


def test_the_latest_reading_is_returned(stat):
    stat.record_reading("hall", 18)
    stat.record_reading("hall", -3)
    assert stat.get_reading("hall") == -3


def test_a_zone_without_readings_raises(stat):
    with pytest.raises(ThermostatError):
        stat.get_reading("hall")


def test_invalid_modes_and_temperatures_are_rejected(stat):
    with pytest.raises(ValueError):
        stat.set_mode("hall", "warm")
    with pytest.raises(ValueError):
        stat.set_target("hall", 21.5)
    assert stat.get_setting("hall") == ("off", 20)


def test_unknown_zones_raise_key_error(stat):
    with pytest.raises(KeyError):
        stat.set_target("garage", 20)
