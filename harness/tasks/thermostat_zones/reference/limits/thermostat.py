"""Thermostat zones with per-zone limits on the target temperature.

Correct solution for thermostat_zones after c_limits.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from thermostat import Thermostat
    stat = Thermostat()
    stat.add_zone("hall")
    stat.set_limits("hall", 15, 25)
    stat.set_target("hall", 22)
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
        self.limits = None  # (low, high) once set
        self.readings = []  # every reading so far, oldest first

    def within_limits(self, temp):
        return self.limits is None or self.limits[0] <= temp <= self.limits[1]


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
        if not z.within_limits(temp):
            raise ValueError(f"target {temp} is outside the limits {z.limits}")
        z.target = temp

    def set_mode(self, zone, mode):
        z = self._require(zone)
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
        z.mode = mode

    def set_limits(self, zone, low, high):
        z = self._require(zone)
        check_temp(low)
        check_temp(high)
        if low > high:
            raise ValueError(f"low {low} is above high {high}")
        if not low <= z.target <= high:
            raise ThermostatError(f"target {z.target} is outside ({low}, {high})")
        z.limits = (low, high)

    def get_limits(self, zone):
        return self._require(zone).limits

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
