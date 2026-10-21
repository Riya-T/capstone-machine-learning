"""Public checks for the c_hold change (zones on hold). Shown to the editor,
never to the writer.

Usage (with thermostat.py importable, e.g. in the sandbox):
    python -m pytest changes/c_hold/public/test_hold_public.py
"""

import pytest
from thermostat import Thermostat, ZoneHeld


def test_a_held_zone_keeps_its_setting():
    s = Thermostat()
    s.add_zone("hall")
    s.set_target("hall", 22)
    s.hold("hall")
    assert s.is_held("hall")
    with pytest.raises(ZoneHeld):
        s.set_target("hall", 25)
    with pytest.raises(ZoneHeld):
        s.set_mode("hall", "heat")
    assert s.get_setting("hall") == ("off", 22)
    s.release("hall")
    s.set_target("hall", 25)
    assert s.get_setting("hall") == ("off", 25)


def test_readings_are_recorded_while_held():
    s = Thermostat()
    s.add_zone("hall")
    s.hold("hall")
    s.record_reading("hall", 19)
    assert s.get_reading("hall") == 19
