"""Public checks for the c_limits change (per-zone target limits). Shown to
the editor, never to the writer.

Usage (with thermostat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_limits/public/test_limits_public.py
"""

import pytest
from thermostat import Thermostat, ThermostatError


def test_targets_outside_the_limits_are_rejected():
    s = Thermostat()
    s.add_zone("bedroom")
    s.set_limits("bedroom", 15, 25)
    assert s.get_limits("bedroom") == (15, 25)
    s.set_target("bedroom", 25)
    with pytest.raises(ValueError):
        s.set_target("bedroom", 26)
    assert s.get_setting("bedroom") == ("off", 25)


def test_zones_start_without_limits():
    s = Thermostat()
    s.add_zone("hall")
    assert s.get_limits("hall") is None
    s.set_target("hall", 40)
    assert s.get_setting("hall") == ("off", 40)


def test_limits_must_include_the_current_target():
    s = Thermostat()
    s.add_zone("hall")
    s.set_target("hall", 30)
    with pytest.raises(ThermostatError):
        s.set_limits("hall", 15, 25)
    assert s.get_limits("hall") is None
