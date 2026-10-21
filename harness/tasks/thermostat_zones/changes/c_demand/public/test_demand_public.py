"""Public checks for the c_demand change (heating and cooling demand). Shown
to the editor, never to the writer.

Usage (with thermostat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_demand/public/test_demand_public.py
"""

from thermostat import Thermostat


def test_heating_demand_is_target_minus_reading():
    s = Thermostat()
    s.add_zone("hall")
    s.set_mode("hall", "heat")
    s.set_target("hall", 22)
    s.record_reading("hall", 18)
    assert s.get_demand("hall") == 4
    assert s.get_total_demand() == 4


def test_a_zone_that_is_off_or_warm_enough_has_no_demand():
    s = Thermostat()
    s.add_zone("hall")
    s.add_zone("attic")
    s.record_reading("hall", 10)
    assert s.get_demand("hall") == 0
    s.set_mode("attic", "heat")
    s.record_reading("attic", 25)
    assert s.get_demand("attic") == 0


def test_calls_count_readings_that_had_demand():
    s = Thermostat()
    s.add_zone("hall")
    s.set_mode("hall", "heat")
    s.record_reading("hall", 18)
    s.record_reading("hall", 21)
    s.record_reading("hall", 19)
    assert s.get_calls("hall") == 2
