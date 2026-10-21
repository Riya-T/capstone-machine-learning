"""Thermostat zones with per-zone target limits and zones that can be put on
hold.

Planted bug (after c_limits and c_hold): holds work, but when set_target
was reworked to check the hold, the limit check was dropped, so targets
outside a zone's limits are accepted again.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from thermostat import Thermostat
    stat = Thermostat()
    stat.add_zone("hall")
    stat.set_limits("hall", 15, 25)
    stat.hold("hall")
"""

MODES = ("heat", "cool", "off")
DEFAULT_TARGET = 20


class ThermostatError(Exception):
    pass


class ZoneHeld(ThermostatError):
    pass


def check_temp(temp):
    if isinstance(temp, bool) or not isinstance(temp, int):
        raise ValueError(f"temperature must be an int, got {temp!r}")


class Zone:
    def __init__(self):
        self.mode = "off"
        self.target = DEFAULT_TARGET
        self.limits = None  # (low, high) once set
        self.held = False
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
        self._require_free(zone, z)
        z.target = temp

    def set_mode(self, zone, mode):
        z = self._require(zone)
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
        self._require_free(zone, z)
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

    def hold(self, zone):
        self._require(zone).held = True

    def release(self, zone):
        self._require(zone).held = False

    def is_held(self, zone):
        return self._require(zone).held

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

    def _require_free(self, zone, z):
        if z.held:
            raise ZoneHeld(f"zone {zone!r} is on hold")
