"""Hidden tests for the initial thermostat_zones spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with thermostat.py importable, e.g. in the sandbox):
    python -m pytest private/test_thermostat_initial.py
"""

import pytest
from thermostat import Thermostat, ThermostatError

BAD_TEMPS = [21.5, "20", None, [20]]
BAD_MODES = ["warm", "", "HEAT", None, 1]


@pytest.fixture
def stat():
    s = Thermostat()
    s.add_zone("hall")
    s.add_zone("attic")
    return s


def state(s):
    """Every zone's setting and latest reading, to check that a failed call changed nothing."""
    result = {}
    for zone in s.get_zones():
        try:
            reading = s.get_reading(zone)
        except ThermostatError:
            reading = None
        result[zone] = (s.get_setting(zone), reading)
    return result


# --- zones ------------------------------------------------------------------


def test_a_new_zone_starts_off_at_the_default_target(stat):
    assert stat.get_setting("hall") == ("off", 20)
    assert stat.get_setting("attic") == ("off", 20)


def test_zones_are_listed_in_the_order_added():
    s = Thermostat()
    for zone in ["kitchen", "attic", "hall"]:
        s.add_zone(zone)
    assert s.get_zones() == ["kitchen", "attic", "hall"]


def test_a_thermostat_starts_with_no_zones():
    assert Thermostat().get_zones() == []


@pytest.mark.parametrize("zone", [""])
def test_empty_zone_names_are_rejected(zone):
    s = Thermostat()
    with pytest.raises(ValueError):
        s.add_zone(zone)
    assert s.get_zones() == []


def test_adding_a_zone_twice_is_rejected_and_keeps_its_state(stat):
    stat.set_target("hall", 25)
    stat.set_mode("hall", "heat")
    stat.record_reading("hall", 19)
    with pytest.raises(ThermostatError):
        stat.add_zone("hall")
    assert stat.get_setting("hall") == ("heat", 25)
    assert stat.get_reading("hall") == 19
    assert stat.get_zones() == ["hall", "attic"]


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.set_target("garage", 20),
        lambda s: s.set_mode("garage", "heat"),
        lambda s: s.record_reading("garage", 20),
        lambda s: s.get_setting("garage"),
        lambda s: s.get_reading("garage"),
        lambda s: s.get_setting(None),
        lambda s: s.set_target(1, 20),
        lambda s: s.record_reading(None, 20),
    ],
)
def test_zones_that_were_not_added_raise_key_error(stat, call):
    stat.record_reading("hall", 18)
    before = state(stat)
    with pytest.raises(KeyError):
        call(stat)
    assert state(stat) == before


# --- settings ---------------------------------------------------------------


def test_set_target_replaces_the_target(stat):
    stat.set_target("hall", 18)
    assert stat.get_setting("hall") == ("off", 18)
    stat.set_target("hall", 24)
    assert stat.get_setting("hall") == ("off", 24)


def test_targets_can_be_negative_or_zero(stat):
    stat.set_target("attic", -5)
    assert stat.get_setting("attic") == ("off", -5)
    stat.set_target("attic", 0)
    assert stat.get_setting("attic") == ("off", 0)


@pytest.mark.parametrize("mode", ["heat", "cool", "off"])
def test_each_mode_can_be_set(stat, mode):
    stat.set_mode("hall", mode)
    assert stat.get_setting("hall") == (mode, 20)


def test_mode_and_target_are_independent(stat):
    stat.set_mode("hall", "cool")
    stat.set_target("hall", 26)
    assert stat.get_setting("hall") == ("cool", 26)
    stat.set_mode("hall", "heat")
    assert stat.get_setting("hall") == ("heat", 26)


def test_zones_keep_separate_settings(stat):
    stat.set_mode("hall", "heat")
    stat.set_target("attic", 15)
    assert stat.get_setting("hall") == ("heat", 20)
    assert stat.get_setting("attic") == ("off", 15)


@pytest.mark.parametrize("temp", BAD_TEMPS)
def test_invalid_targets_are_rejected(stat, temp):
    before = state(stat)
    with pytest.raises(ValueError):
        stat.set_target("hall", temp)
    assert state(stat) == before


@pytest.mark.parametrize("mode", BAD_MODES)
def test_invalid_modes_are_rejected(stat, mode):
    stat.set_mode("hall", "heat")
    before = state(stat)
    with pytest.raises(ValueError):
        stat.set_mode("hall", mode)
    assert state(stat) == before


# --- readings ---------------------------------------------------------------


def test_the_most_recent_reading_is_returned(stat):
    stat.record_reading("hall", 17)
    assert stat.get_reading("hall") == 17
    stat.record_reading("hall", 19)
    stat.record_reading("hall", 18)
    assert stat.get_reading("hall") == 18


def test_readings_are_kept_per_zone(stat):
    stat.record_reading("hall", 17)
    stat.record_reading("attic", 30)
    assert stat.get_reading("hall") == 17
    assert stat.get_reading("attic") == 30


def test_no_reading_yet_raises(stat):
    stat.record_reading("hall", 17)
    with pytest.raises(ThermostatError):
        stat.get_reading("attic")


def test_readings_are_not_limited_by_target_or_mode(stat):
    stat.set_mode("hall", "heat")
    stat.set_target("hall", 20)
    stat.record_reading("hall", 45)
    assert stat.get_reading("hall") == 45
    stat.record_reading("hall", -20)
    assert stat.get_reading("hall") == -20


def test_readings_do_not_change_the_setting(stat):
    stat.record_reading("hall", 5)
    assert stat.get_setting("hall") == ("off", 20)


@pytest.mark.parametrize("temp", BAD_TEMPS)
def test_invalid_readings_are_rejected(stat, temp):
    stat.record_reading("hall", 18)
    before = state(stat)
    with pytest.raises(ValueError):
        stat.record_reading("hall", temp)
    assert state(stat) == before


def test_a_missing_zone_is_reported_before_a_bad_value(stat):
    with pytest.raises(KeyError):
        stat.set_target("garage", "hot")
    with pytest.raises(KeyError):
        stat.set_mode("garage", "warm")
    with pytest.raises(KeyError):
        stat.record_reading("garage", None)


def test_thermostats_do_not_share_zones():
    first, second = Thermostat(), Thermostat()
    first.add_zone("hall")
    first.set_target("hall", 25)
    assert second.get_zones() == []
    second.add_zone("hall")
    assert second.get_setting("hall") == ("off", 20)
