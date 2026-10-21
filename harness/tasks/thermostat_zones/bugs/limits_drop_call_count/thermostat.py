"""Thermostat zones with heating and cooling demand and per-zone limits on
the target temperature.

Planted bug (after c_demand and c_limits): limits work, but record_reading
was rewritten while adding them and no longer counts readings that had
demand, so get_calls stays at 0.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from thermostat import Thermostat
    stat = Thermostat()
    stat.add_zone("hall")
    stat.set_limits("hall", 15, 25)
    stat.set_mode("hall", "heat")
    stat.record_reading("hall", 18)
    stat.get_demand("hall")
"""

MODES = ("heat", "cool", "off")
DEFAULT_TARGET = 20


class ThermostatError(Exception):
    pass


def check_temp(temp):
    if isinstance(temp, bool) or not isinstance(temp, int):
        raise ValueError(f"temperature must be an int, got {temp!r}")


def demand_for(mode, target, reading):
    """How far a reading is from the target on the side the mode cares about."""
    if mode == "heat":
        return max(0, target - reading)
    if mode == "cool":
        return max(0, reading - target)
    return 0


class Zone:
    def __init__(self):
        self.mode = "off"
        self.target = DEFAULT_TARGET
        self.limits = None  # (low, high) once set
        self.readings = []  # every reading so far, oldest first
        self.calls = 0  # readings recorded while the zone had demand

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

    def get_demand(self, zone):
        z = self._require(zone)
        if not z.readings:
            return 0
        return demand_for(z.mode, z.target, z.readings[-1])

    def get_total_demand(self):
        return sum(self.get_demand(zone) for zone in self._zones)

    def get_calls(self, zone):
        return self._require(zone).calls

    def get_zones(self):
        return list(self._zones)

    def _require(self, zone):
        # Non-str zones are never stored, so they count as "not added" too.
        if not isinstance(zone, str) or zone not in self._zones:
            raise KeyError(zone)
        return self._zones[zone]
