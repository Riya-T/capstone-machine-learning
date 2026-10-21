"""Thermostat zones: a target temperature, a mode and sensor readings per zone.

Correct solution for thermostat_zones before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from thermostat import Thermostat
    stat = Thermostat()
    stat.add_zone("hall")
    stat.set_mode("hall", "heat")
    stat.record_reading("hall", 18)
"""

MODES = ("heat", "cool", "off")
DEFAULT_TARGET = 20


class ThermostatError(Exception):
    pass


def check_temp(temp):
    if isinstance(temp, bool) or not isinstance(temp, int):
        raise ValueError(f"temperature must be an int, got {temp!r}")


class Zone:
    def __init__(self):
        self.mode = "off"
        self.target = DEFAULT_TARGET
        self.readings = []  # every reading so far, oldest first


class Thermostat:
    def __init__(self):
        self._zones = {}  # zone name -> Zone, in the order added

    def add_zone(self, zone):
        if not isinstance(zone, str) or not zone:
            raise ValueError("zone must be a non-empty str")
        if zone in self._zones:
            raise ThermostatError(f"zone {zone!r} was already added")
        self._zones[zone] = Zone()

    def set_target(self, zone, temp):
        z = self._require(zone)
        check_temp(temp)
        z.target = temp

    def set_mode(self, zone, mode):
        z = self._require(zone)
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
        z.mode = mode

    def record_reading(self, zone, temp):
        z = self._require(zone)
        check_temp(temp)
        z.readings.append(temp)

    def get_setting(self, zone):
        z = self._require(zone)
        return (z.mode, z.target)

    def get_reading(self, zone):
        z = self._require(zone)
        if not z.readings:
            raise ThermostatError(f"zone {zone!r} has no reading yet")
        return z.readings[-1]

    def get_zones(self):
        return list(self._zones)

    def _require(self, zone):
        # Non-str zones are never stored, so they count as "not added" too.
        if not isinstance(zone, str) or zone not in self._zones:
            raise KeyError(zone)
        return self._zones[zone]
