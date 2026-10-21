"""Hidden tests for the c_demand change (heating and cooling demand). Never
shown to the writer or the editor.

Usage (with thermostat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_demand/private/test_demand_new.py
"""

import pytest
from thermostat import Thermostat


@pytest.fixture
def stat():
    s = Thermostat()
    s.add_zone("hall")
    s.add_zone("attic")
    s.add_zone("cellar")
    s.set_mode("hall", "heat")
    s.set_target("hall", 22)
    s.set_mode("attic", "cool")
    s.set_target("attic", 24)
    return s


def test_demand_without_a_reading_is_zero(stat):
    assert stat.get_demand("hall") == 0
    assert stat.get_demand("attic") == 0
    assert stat.get_total_demand() == 0


def test_heat_demand_follows_the_latest_reading(stat):
    stat.record_reading("hall", 15)
    assert stat.get_demand("hall") == 7
    stat.record_reading("hall", 20)
    assert stat.get_demand("hall") == 2
    stat.record_reading("hall", 22)
    assert stat.get_demand("hall") == 0


def test_cool_demand_is_reading_minus_target(stat):
    stat.record_reading("attic", 30)
    assert stat.get_demand("attic") == 6
    stat.record_reading("attic", 24)
    assert stat.get_demand("attic") == 0


def test_a_reading_on_the_wrong_side_gives_zero_not_negative(stat):
    stat.record_reading("hall", 28)
    stat.record_reading("attic", 10)
    assert stat.get_demand("hall") == 0
    assert stat.get_demand("attic") == 0


def test_off_zones_never_have_demand(stat):
    stat.record_reading("cellar", -10)
    assert stat.get_demand("cellar") == 0
    stat.set_mode("hall", "off")
    stat.record_reading("hall", 5)
    assert stat.get_demand("hall") == 0


def test_demand_changes_with_the_mode_and_target(stat):
    stat.record_reading("hall", 18)
    assert stat.get_demand("hall") == 4
    stat.set_target("hall", 25)
    assert stat.get_demand("hall") == 7
    stat.set_mode("hall", "cool")
    assert stat.get_demand("hall") == 0
    stat.set_target("hall", 10)
    assert stat.get_demand("hall") == 8


def test_negative_temperatures_work(stat):
    stat.set_target("hall", -5)
    stat.record_reading("hall", -12)
    assert stat.get_demand("hall") == 7


def test_total_demand_adds_every_zone(stat):
    stat.record_reading("hall", 17)
    stat.record_reading("attic", 27)
    stat.record_reading("cellar", 0)
    assert stat.get_total_demand() == 5 + 3


def test_total_demand_with_no_zones_is_zero():
    assert Thermostat().get_total_demand() == 0


def test_calls_start_at_zero(stat):
    assert stat.get_calls("hall") == 0
    stat.record_reading("hall", 22)
    assert stat.get_calls("hall") == 0


def test_calls_count_readings_with_demand_in_either_mode(stat):
    for temp in [18, 22, 23, 19]:
        stat.record_reading("hall", temp)
    assert stat.get_calls("hall") == 2
    for temp in [26, 24, 25]:
        stat.record_reading("attic", temp)
    assert stat.get_calls("attic") == 2


def test_calls_use_the_setting_in_force_when_recorded(stat):
    stat.record_reading("hall", 18)  # demand 4 under heat/22
    stat.set_mode("hall", "off")
    stat.record_reading("hall", 10)  # off: no demand
    stat.set_mode("hall", "heat")
    stat.set_target("hall", 5)
    stat.record_reading("hall", 10)  # target 5: no demand
    assert stat.get_calls("hall") == 1
    stat.set_target("hall", 30)  # does not rewrite the past
    assert stat.get_calls("hall") == 1
    assert stat.get_demand("hall") == 20


def test_off_zone_readings_are_never_calls(stat):
    for temp in [-10, 0, 40]:
        stat.record_reading("cellar", temp)
    assert stat.get_calls("cellar") == 0


@pytest.mark.parametrize("zone", ["garage", None, 1])
def test_demand_methods_need_an_added_zone(stat, zone):
    with pytest.raises(KeyError):
        stat.get_demand(zone)
    with pytest.raises(KeyError):
        stat.get_calls(zone)
